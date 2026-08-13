from __future__ import annotations

import csv
import io
import math
from typing import Any

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Query, Session

from app.core.exceptions import ResourceNotFoundError
from app.logger import logger
from app.models.asset import Asset
from app.models.finding import Finding
from app.models.finding_activity import FindingActivity
from app.models.scan import Scan
from app.models.scan_result import ScanResult
from app.models.user import User
from app.services.query_helpers import apply_asset_scope
from app.ws.hub import scan_event_hub
from app.services.notification_service import notify_finding_assignment
from app.services.activity_service import record_activity

_UNSET = object()

_FINDING_CSV_COLUMNS = [
    "id",
    "cve",
    "title",
    "severity",
    "cvss",
    "status",
    "asset",
    "service",
    "assigned_to",
    "due_date",
    "created_at",
    "updated_at",
]


def _publish_finding_event(
    finding: Finding,
    owner_user_id: int,
) -> None:
    scan_event_hub.publish(
        {
            "type": "finding.updated",
            "finding_id": finding.id,
            "status": finding.status,
            "user_id": owner_user_id,
        }
    )


def _record_activity(
    db: Session,
    finding: Finding,
    actor: User,
    action: str,
    old_value: str | None,
    new_value: str | None,
) -> None:
    db.add(
        FindingActivity(
            finding_id=finding.id,
            user_id=actor.id,
            action=action,
            old_value=old_value,
            new_value=new_value,
        )
    )


def create_findings(
    db: Session,
    scan_result: ScanResult,
    cves: list[dict],
) -> list[Finding]:
    """
    Create Finding records from CVEs returned by the intelligence layer.

    CVEs already recorded against this scan result, and duplicate CVEs
    within the payload, are skipped so re-runs never double-insert.
    """

    existing = {
        row[0]
        for row in db.query(Finding.cve).filter(
            Finding.scan_result_id == scan_result.id,
        ).all()
        if row[0]
    }

    findings: list[Finding] = []
    seen: set[str] = set()

    for vuln in cves:
        cve = vuln.get("cve", {})
        cve_id = cve.get("id")

        if not cve_id:
            continue

        if cve_id in existing or cve_id in seen:
            continue

        seen.add(cve_id)

        descriptions = cve.get("descriptions", [])
        description = (
            descriptions[0].get("value", "")
            if descriptions
            else ""
        )

        metrics = cve.get("metrics", {})

        severity = "UNKNOWN"
        cvss = None

        if "cvssMetricV40" in metrics:
            metric = metrics["cvssMetricV40"][0]
            severity = metric.get("baseSeverity", "UNKNOWN")
            cvss = metric["cvssData"].get("baseScore")

        elif "cvssMetricV31" in metrics:
            metric = metrics["cvssMetricV31"][0]
            severity = metric.get("baseSeverity", "UNKNOWN")
            cvss = metric["cvssData"].get("baseScore")

        elif "cvssMetricV30" in metrics:
            metric = metrics["cvssMetricV30"][0]
            severity = metric.get("baseSeverity", "UNKNOWN")
            cvss = metric["cvssData"].get("baseScore")

        elif "cvssMetricV2" in metrics:
            metric = metrics["cvssMetricV2"][0]
            severity = metric.get("baseSeverity", "UNKNOWN")
            cvss = metric["cvssData"].get("baseScore")

        finding = Finding(
            scan_result_id=scan_result.id,
            title=cve_id,
            severity=severity,
            cpe=scan_result.cpe,
            cve=cve_id,
            cvss=cvss,
            description=description,
            recommendation="Update to the latest supported version.",
            status="OPEN",
        )

        db.add(finding)
        findings.append(finding)

    db.flush()

    return findings


# ---------------------------------------------------------------------
# Query Helpers
# ---------------------------------------------------------------------


def _base_findings_query(
    db: Session,
    current_user: User,
) -> Query:
    """
    Base findings query with joins and ownership filtering applied.
    """

    query = (
        db.query(Finding)
        .join(
            ScanResult,
            Finding.scan_result_id == ScanResult.id,
        )
        .join(
            Scan,
            ScanResult.scan_id == Scan.id,
        )
        .join(
            Asset,
            Scan.asset_id == Asset.id,
        )
        .outerjoin(
            User,
            Finding.assigned_to == User.id,
        )
    )

    return apply_asset_scope(
        query,
        current_user,
    )


def _severity_rank_expression():
    return case(
        (Finding.severity == "CRITICAL", 4),
        (Finding.severity == "HIGH", 3),
        (Finding.severity == "MEDIUM", 2),
        (Finding.severity == "LOW", 1),
        else_=0,
    )


def _apply_findings_filters(
    query: Query,
    severity: str | None,
    status: str | None,
    asset: str | None,
    scan: int | None,
    cve: str | None,
    search: str | None,
    assigned: str | None = None,
    current_user: User | None = None,
) -> Query:

    if severity:
        query = query.filter(
            Finding.severity.ilike(f"%{severity}%")
        )

    if status:
        query = query.filter(
            Finding.status == status
        )

    if asset:
        query = query.filter(
            Asset.name.ilike(f"%{asset}%")
        )

    if scan:
        query = query.filter(
            Scan.id == scan
        )

    if cve:
        query = query.filter(
            Finding.cve.ilike(f"%{cve}%")
        )

    if assigned == "me" and current_user is not None:
        query = query.filter(
            Finding.assigned_to == current_user.id,
        )

    if assigned == "unassigned":
        query = query.filter(
            Finding.assigned_to.is_(None),
        )

    if search:
        search_term = f"%{search}%"

        query = query.filter(
            or_(
                Finding.cve.ilike(search_term),
                Finding.title.ilike(search_term),
                Asset.name.ilike(search_term),
            )
        )

    return query


def _apply_findings_sort(
    query: Query,
    sort_by: str,
    sort_order: str,
) -> Query:

    ascending = sort_order == "asc"

    if sort_by == "severity":
        severity = _severity_rank_expression()

        return query.order_by(
            severity.asc() if ascending else severity.desc()
        )

    if sort_by == "asset":
        return query.order_by(
            Asset.name.asc() if ascending else Asset.name.desc()
        )

    if sort_by == "status":
        return query.order_by(
            Finding.status.asc()
            if ascending
            else Finding.status.desc()
        )

    if sort_by == "title":
        return query.order_by(
            Finding.title.asc()
            if ascending
            else Finding.title.desc()
        )

    if sort_by == "cve":
        return query.order_by(
            Finding.cve.asc()
            if ascending
            else Finding.cve.desc()
        )

    return query.order_by(
        Finding.created_at.asc()
        if ascending
        else Finding.created_at.desc()
    )
def get_findings(
    db: Session,
    current_user: User,
    severity: str | None = None,
    status: str | None = None,
    asset: str | None = None,
    scan: int | None = None,
    cve: str | None = None,
    search: str | None = None,
    assigned: str | None = None,
    page: int = 1,
    size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> dict[str, Any]:
    """
    Return a paginated, filterable, searchable collection of findings.
    """

    query = (
        _base_findings_query(
            db,
            current_user,
        )
        .with_entities(
            Finding.id,
            Finding.title,
            Finding.severity,
            Finding.cve,
            Finding.cvss,
            Finding.status,
            Finding.assigned_to,
            Finding.due_date,
            Finding.created_at,
            Finding.updated_at,
            Asset.name.label("asset_name"),
            ScanResult.service.label("affected_service"),
            User.username.label("assigned_to_name"),
        )
    )

    query = _apply_findings_filters(
        query=query,
        severity=severity,
        status=status,
        asset=asset,
        scan=scan,
        cve=cve,
        search=search,
        assigned=assigned,
        current_user=current_user,
    )

    total = query.count()

    query = _apply_findings_sort(
        query,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    offset = (page - 1) * size

    rows = (
        query.offset(offset)
        .limit(size)
        .all()
    )

    items = [
        {
            "id": row.id,
            "title": row.title,
            "severity": row.severity,
            "cve": row.cve,
            "cvss": row.cvss,
            "status": row.status,
            "assigned_to": row.assigned_to,
            "assigned_to_name": row.assigned_to_name,
            "due_date": row.due_date,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "asset_name": row.asset_name,
            "affected_service": row.affected_service,
        }
        for row in rows
    ]

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": math.ceil(total / size) if total else 0,
    }


def get_finding(
    db: Session,
    finding_id: int,
    current_user: User,
) -> dict[str, Any] | None:
    """
    Return a single finding for the detail page.
    """

    finding = (
        _base_findings_query(
            db,
            current_user,
        )
        .with_entities(
            Finding.id,
            Finding.title,
            Finding.description,
            Finding.severity,
            Finding.cve,
            Finding.cvss,
            Finding.recommendation,
            Finding.status,
            Finding.assigned_to,
            Finding.notes,
            Finding.due_date,
            Finding.created_at,
            Finding.updated_at,
            Asset.name.label("affected_asset"),
            ScanResult.service.label("affected_service"),
            User.username.label("assigned_to_name"),
        )
        .filter(
            Finding.id == finding_id,
        )
        .first()
    )

    if finding is None:
        return None

    return {
        "id": finding.id,
        "title": finding.title,
        "description": finding.description,
        "severity": finding.severity,
        "cve": finding.cve,
        "cvss": finding.cvss,
        "affected_asset": finding.affected_asset,
        "affected_service": finding.affected_service,
        "recommendation": finding.recommendation,
        "status": finding.status,
        "assigned_to": finding.assigned_to,
        "assigned_to_name": finding.assigned_to_name,
        "notes": finding.notes,
        "due_date": finding.due_date,
        "created_at": finding.created_at,
        "updated_at": finding.updated_at,
        "provider": "NVD",
        "lookup_method": "cpeName/keywordSearch",
        "confidence": (
            "MEDIUM"
            if finding.cve
            else None
        ),
    }


def _scoped_finding(
    db: Session,
    finding_id: int,
    current_user: User,
) -> Finding | None:
    """
    Fetch a finding restricted to the current user's asset scope.
    """

    return (
        _base_findings_query(
            db,
            current_user,
        )
        .filter(
            Finding.id == finding_id,
        )
        .first()
    )


def update_finding_status(
    db: Session,
    finding_id: int,
    status: str,
    current_user: User,
) -> dict[str, Any] | None:
    """
    Update a finding status.

    Backwards-compatible wrapper around :func:`update_finding_triage`.
    """

    return update_finding_triage(
        db,
        finding_id,
        current_user,
        status=status,
    )


def update_finding_triage(
    db: Session,
    finding_id: int,
    current_user: User,
    *,
    status: Any = _UNSET,
    assignee_id: Any = _UNSET,
    notes: Any = _UNSET,
    due_date: Any = _UNSET,
) -> dict[str, Any] | None:
    """
    Update triage fields on a finding: status, assignee, notes, due date.

    Field changes are recorded in the finding activity log. Returns the
    updated finding or ``None`` when out of scope / missing.
    """

    finding = _scoped_finding(
        db,
        finding_id,
        current_user,
    )

    if finding is None:
        return None

    if status is not _UNSET:
        new_status = status.value if hasattr(status, "value") else str(status)

        if new_status != finding.status:
            _record_activity(
                db,
                finding,
                current_user,
                "status",
                finding.status,
                new_status,
            )
            finding.status = new_status

            if new_status in ("RESOLVED", "FALSE_POSITIVE", "ACCEPTED_RISK"):
                record_activity(
                    db,
                    user_id=current_user.id,
                    action="finding_closed",
                    entity_type="finding",
                    entity_id=finding.id,
                    detail=f"{finding.cve or finding.title} marked {new_status}",
                )

    if assignee_id is not _UNSET:
        old_assignee = (
            f"user:{finding.assigned_to}"
            if finding.assigned_to
            else None
        )

        if assignee_id is None:
            if finding.assigned_to is not None:
                _record_activity(
                    db,
                    finding,
                    current_user,
                    "assignee",
                    old_assignee,
                    None,
                )
            finding.assigned_to = None
        else:
            assignee = (
                db.query(User)
                .filter(
                    User.id == assignee_id,
                    User.is_active.is_(True),
                )
                .first()
            )

            if assignee is None:
                raise ResourceNotFoundError(
                    "Assignee not found."
                )

            if finding.assigned_to != assignee_id:
                _record_activity(
                    db,
                    finding,
                    current_user,
                    "assignee",
                    old_assignee,
                    f"user:{assignee.id}",
                )
                notify_finding_assignment(
                    db,
                    finding,
                    assignee.id,
                    current_user,
                )
                record_activity(
                    db,
                    user_id=current_user.id,
                    action="finding_assigned",
                    entity_type="finding",
                    entity_id=finding.id,
                    detail=f"{finding.cve or finding.title} assigned to {assignee.username}",
                    meta={"assignee_id": assignee.id},
                )
            finding.assigned_to = assignee.id

    if notes is not _UNSET:
        new_notes = notes or None

        if new_notes != finding.notes:
            _record_activity(
                db,
                finding,
                current_user,
                "notes",
                finding.notes,
                new_notes,
            )
        finding.notes = new_notes

    if due_date is not _UNSET and due_date != finding.due_date:
        old_due = (
            finding.due_date.isoformat()
            if finding.due_date
            else None
        )
        new_due = (
            due_date.isoformat()
            if due_date
            else None
        )

        if old_due != new_due:
            _record_activity(
                db,
                finding,
                current_user,
                "due_date",
                old_due,
                new_due,
            )
        finding.due_date = due_date

    db.commit()
    db.refresh(finding)

    logger.info(
        "Finding triage updated: %s by %s",
        finding_id,
        current_user.username,
    )

    _publish_finding_event(finding, current_user.id)

    return get_finding(
        db,
        finding_id,
        current_user,
    )


def bulk_update_findings_status(
    db: Session,
    finding_ids: list[int],
    status: str,
    current_user: User,
) -> dict[str, Any]:
    """
    Apply a status change to a batch of findings within the user's scope.

    Returns the number of findings updated and the ids that changed.
    """

    findings = (
        _base_findings_query(
            db,
            current_user,
        )
        .filter(
            Finding.id.in_(finding_ids),
        )
        .all()
    )

    updated: list[int] = []

    for finding in findings:
        if finding.status == status:
            continue

        _record_activity(
            db,
            finding,
            current_user,
            "status",
            finding.status,
            status,
        )
        finding.status = status
        updated.append(finding.id)

    db.commit()

    for finding in findings:
        if finding.id in updated:
            _publish_finding_event(finding, current_user.id)

    logger.info(
        "Bulk status update: %s findings -> %s by %s",
        len(updated),
        status,
        current_user.username,
    )

    return {
        "updated": len(updated),
        "ids": updated,
    }


def get_finding_activities(
    db: Session,
    finding_id: int,
    current_user: User,
) -> list[dict[str, Any]] | None:
    """
    Return the audit trail for a finding, most recent first.
    """

    finding = _scoped_finding(
        db,
        finding_id,
        current_user,
    )

    if finding is None:
        return None

    rows = (
        db.query(
            FindingActivity.id,
            FindingActivity.finding_id,
            FindingActivity.user_id,
            FindingActivity.action,
            FindingActivity.old_value,
            FindingActivity.new_value,
            FindingActivity.created_at,
            User.username.label("username"),
        )
        .outerjoin(
            User,
            FindingActivity.user_id == User.id,
        )
        .filter(
            FindingActivity.finding_id == finding_id,
        )
        .order_by(
            FindingActivity.created_at.desc(),
        )
        .all()
    )

    return [
        {
            "id": row.id,
            "finding_id": row.finding_id,
            "user_id": row.user_id,
            "username": row.username,
            "action": row.action,
            "old_value": row.old_value,
            "new_value": row.new_value,
            "created_at": row.created_at,
        }
        for row in rows
    ]


def list_findings_assignees(db: Session) -> list[dict[str, Any]]:
    """
    Return active users available as finding assignees.
    """

    users = (
        db.query(
            User.id,
            User.username,
        )
        .filter(
            User.is_active.is_(True),
        )
        .order_by(
            User.username.asc(),
        )
        .all()
    )

    return [
        {
            "id": user.id,
            "username": user.username,
        }
        for user in users
    ]


def get_findings_stats(
    db: Session,
    current_user: User,
) -> dict[str, Any]:
    """
    Return status/severity rollups for the triage dashboard row.
    """

    base = _base_findings_query(db, current_user)

    status_rows = (
        base.with_entities(
            Finding.status,
            func.count(),
        )
        .group_by(Finding.status)
        .all()
    )

    severity_rows = (
        base.with_entities(
            Finding.severity,
            func.count(),
        )
        .group_by(Finding.severity)
        .all()
    )

    status_counts = {
        status: count
        for status, count in status_rows
    }

    total = sum(status_counts.values())

    return {
        "total": total,
        "open": status_counts.get("OPEN", 0),
        "in_progress": status_counts.get("IN_PROGRESS", 0),
        "resolved": status_counts.get("RESOLVED", 0),
        "false_positive": status_counts.get("FALSE_POSITIVE", 0),
        "accepted_risk": status_counts.get("ACCEPTED_RISK", 0),
        "by_severity": {
            severity: count
            for severity, count in severity_rows
        },
    }


def export_findings_csv(
    db: Session,
    current_user: User,
    severity: str | None = None,
    status: str | None = None,
    asset: str | None = None,
    scan: int | None = None,
    cve: str | None = None,
    search: str | None = None,
    assigned: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> str:
    """
    Build a CSV document of findings within the user's scope.
    """

    query = (
        _base_findings_query(
            db,
            current_user,
        )
        .with_entities(
            Finding.id,
            Finding.cve,
            Finding.title,
            Finding.severity,
            Finding.cvss,
            Finding.status,
            Finding.assigned_to,
            Finding.due_date,
            Finding.created_at,
            Finding.updated_at,
            Asset.name.label("asset"),
            ScanResult.service.label("service"),
            User.username.label("assigned_to_name"),
        )
    )

    query = _apply_findings_filters(
        query=query,
        severity=severity,
        status=status,
        asset=asset,
        scan=scan,
        cve=cve,
        search=search,
        assigned=assigned,
        current_user=current_user,
    )

    query = _apply_findings_sort(
        query,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow(_FINDING_CSV_COLUMNS)

    for row in query.all():
        writer.writerow(
            [
                row.id,
                row.cve or "",
                row.title,
                row.severity,
                row.cvss or "",
                row.status,
                row.asset,
                row.service or "",
                row.assigned_to_name or "",
                (
                    row.due_date.isoformat()
                    if row.due_date
                    else ""
                ),
                (
                    row.created_at.isoformat()
                    if row.created_at
                    else ""
                ),
                (
                    row.updated_at.isoformat()
                    if row.updated_at
                    else ""
                ),
            ]
        )

    return buffer.getvalue()
