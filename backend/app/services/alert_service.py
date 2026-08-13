from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.asset import Asset
from app.models.finding import Finding
from app.models.incident import Incident
from app.models.scan import Scan
from app.models.scan_result import ScanResult
from app.models.user import User
from app.services.activity_service import record_activity
from app.ws.hub import scan_event_hub

ALERT_STATUS_OPEN = "OPEN"
ALERT_STATUS_ACKNOWLEDGED = "ACKNOWLEDGED"
ALERT_STATUS_RESOLVED = "RESOLVED"

INCIDENT_STATUS_OPEN = "OPEN"
INCIDENT_STATUS_INVESTIGATING = "INVESTIGATING"
INCIDENT_STATUS_MITIGATED = "MITIGATED"
INCIDENT_STATUS_RESOLVED = "RESOLVED"

# Alert types produced by the trigger rules.
ALERT_TYPES = {
    "critical_vuln",
    "high_epss",
    "kev",
    "malicious_vt",
    "scan_failed",
    "asset_offline",
    "scan_completed",
}


def _publish_alert_event(alert: Alert) -> None:
    scan_event_hub.publish(
        {
            "type": "alert.created",
            "alert_id": alert.id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "user_id": alert.user_id,
        }
    )


def create_alert(
    db: Session,
    *,
    user_id: int,
    alert_type: str,
    title: str,
    body: str | None = None,
    severity: str = "INFO",
    source: str = "system",
    finding_id: int | None = None,
    asset_id: int | None = None,
) -> Alert:
    if alert_type not in ALERT_TYPES:
        alert_type = "critical_vuln"

    alert = Alert(
        user_id=user_id,
        alert_type=alert_type,
        title=title,
        body=body,
        severity=severity,
        source=source,
        finding_id=finding_id,
        asset_id=asset_id,
        status=ALERT_STATUS_OPEN,
    )

    db.add(alert)
    db.flush()

    _publish_alert_event(alert)

    return alert


def list_alerts(
    db: Session,
    user_id: int,
    *,
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    severity: str | None = None,
) -> dict[str, Any]:
    query = db.query(Alert).filter(Alert.user_id == user_id)

    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)

    total = query.count()

    rows = (
        query.order_by(
            Alert.created_at.desc(),
            Alert.id.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    open_count = (
        db.query(Alert)
        .filter(
            Alert.user_id == user_id,
            Alert.status == ALERT_STATUS_OPEN,
        )
        .count()
    )

    return {
        "items": rows,
        "total": total,
        "open": open_count,
    }


def get_alert(
    db: Session,
    alert_id: int,
    user_id: int,
) -> Alert | None:
    return (
        db.query(Alert)
        .filter(
            Alert.id == alert_id,
            Alert.user_id == user_id,
        )
        .first()
    )


def update_alert_status(
    db: Session,
    alert: Alert,
    status: str,
) -> Alert:
    now = datetime.now(UTC)

    if status == ALERT_STATUS_ACKNOWLEDGED:
        alert.acknowledged_at = alert.acknowledged_at or now
        alert.status = status
    elif status == ALERT_STATUS_RESOLVED:
        alert.resolved_at = now
        alert.status = status
    else:
        alert.status = status

    db.commit()
    db.refresh(alert)

    return alert


def create_incident(
    db: Session,
    *,
    user_id: int,
    title: str,
    description: str | None = None,
    severity: str = "MEDIUM",
    status: str = INCIDENT_STATUS_OPEN,
    asset_id: int | None = None,
    alert_id: int | None = None,
    finding_id: int | None = None,
    assignee_id: int | None = None,
) -> Incident:
    incident = Incident(
        user_id=user_id,
        title=title,
        description=description,
        severity=severity,
        status=status,
        asset_id=asset_id,
        alert_id=alert_id,
        finding_id=finding_id,
        assignee_id=assignee_id,
    )

    db.add(incident)
    db.flush()

    if alert_id is not None:
        alert = get_alert(db, alert_id, user_id)
        if alert is not None:
            alert.status = ALERT_STATUS_RESOLVED
            alert.resolved_at = datetime.now(UTC)

    record_activity(
        db,
        user_id=user_id,
        action="incident_created",
        entity_type="incident",
        entity_id=incident.id,
        detail=f"Created incident: {incident.title}",
        meta={"severity": severity, "alert_id": alert_id},
    )

    db.commit()
    db.refresh(incident)

    return incident


def list_incidents(
    db: Session,
    user_id: int,
    *,
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    severity: str | None = None,
) -> dict[str, Any]:
    query = db.query(Incident).filter(Incident.user_id == user_id)

    if status:
        query = query.filter(Incident.status == status)
    if severity:
        query = query.filter(Incident.severity == severity)

    total = query.count()

    open_count = (
        db.query(Incident)
        .filter(
            Incident.user_id == user_id,
            Incident.status.in_([INCIDENT_STATUS_OPEN, INCIDENT_STATUS_INVESTIGATING]),
        )
        .count()
    )

    rows = (
        query.order_by(
            Incident.created_at.desc(),
            Incident.id.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "items": rows,
        "total": total,
        "open": open_count,
    }


def get_incident(
    db: Session,
    incident_id: int,
    user_id: int,
) -> Incident | None:
    return (
        db.query(Incident)
        .filter(
            Incident.id == incident_id,
            Incident.user_id == user_id,
        )
        .first()
    )


def update_incident(
    db: Session,
    incident: Incident,
    *,
    status: str | None = None,
    assignee_id: int | None = None,
    summary: str | None = None,
    actor: User,
) -> Incident:
    if status is not None:
        incident.status = status
        if status == INCIDENT_STATUS_RESOLVED:
            incident.resolved_at = datetime.now(UTC)

    if assignee_id is not None:
        incident.assignee_id = assignee_id

    if summary is not None:
        incident.summary = summary

    record_activity(
        db,
        user_id=actor.id,
        action="incident_updated",
        entity_type="incident",
        entity_id=incident.id,
        detail=f"Updated incident: {incident.title}",
        meta={"status": status},
    )

    db.commit()
    db.refresh(incident)

    return incident


def delete_incident(
    db: Session,
    incident: Incident,
) -> None:
    db.delete(incident)
    db.commit()


# ---------------------------------------------------------------------
# Trigger rules
# ---------------------------------------------------------------------


def evaluate_finding_alert(
    db: Session,
    finding: Finding,
    *,
    user_id: int,
    epss_score: float | None = None,
    in_kev: bool = False,
) -> Alert | None:
    """
    Create an alert for a high-impact finding based on its severity and
    threat-intelligence signals (EPSS probability, KEV membership).
    """

    if finding.severity == "CRITICAL":
        return create_alert(
            db,
            user_id=user_id,
            alert_type="critical_vuln",
            title=f"Critical vulnerability: {finding.cve or finding.title}",
            body=f"CVSS {finding.cvss:.1f}" if finding.cvss else None,
            severity="CRITICAL",
            source="scan",
            finding_id=finding.id,
            asset_id=_finding_asset_id(db, finding),
        )

    if in_kev:
        return create_alert(
            db,
            user_id=user_id,
            alert_type="kev",
            title=f"Known-exploited vulnerability: {finding.cve or finding.title}",
            body="This CVE is listed in CISA's Known Exploited Vulnerabilities catalog.",
            severity="HIGH",
            source="kev",
            finding_id=finding.id,
            asset_id=_finding_asset_id(db, finding),
        )

    if epss_score is not None and epss_score >= 0.9:
        return create_alert(
            db,
            user_id=user_id,
            alert_type="high_epss",
            title=f"High EPSS: {finding.cve or finding.title}",
            body=f"{epss_score:.1%} probability of exploitation within 30 days.",
            severity="HIGH",
            source="epss",
            finding_id=finding.id,
            asset_id=_finding_asset_id(db, finding),
        )

    return None


def _finding_asset_id(
    db: Session,
    finding: Finding,
) -> int | None:
    scan = (
        db.query(Scan.asset_id)
        .join(ScanResult, ScanResult.scan_id == Scan.id)
        .filter(ScanResult.id == finding.scan_result_id)
        .first()
    )

    return scan[0] if scan else None


def notify_scan_outcome_alert(
    db: Session,
    scan: Scan,
    asset: Asset,
    *,
    success: bool,
) -> Alert | None:
    """Create an alert when a scan fails or completes on an asset."""
    if success:
        return None

    return create_alert(
        db,
        user_id=asset.created_by,
        alert_type="scan_failed",
        title=f"Scan failed on {asset.name}",
        body=f"Scan #{scan.id} did not complete. Review the scan logs for details.",
        severity="HIGH",
        source="scan",
        asset_id=asset.id,
    )


def notify_malicious_ioc_alert(
    db: Session,
    user_id: int,
    *,
    value: str,
    malicious_count: int,
    risk_score: float,
) -> Alert:
    return create_alert(
        db,
        user_id=user_id,
        alert_type="malicious_vt",
        title=f"Malicious IOC detected: {value}",
        body=(
            f"{malicious_count} vendor(s) flagged this indicator "
            f"(risk score {risk_score:.1f})."
        ),
        severity="CRITICAL" if malicious_count >= 5 else "HIGH",
        source="virustotal",
    )


def alert_summary(
    db: Session,
    user_id: int,
) -> dict[str, Any]:
    """Counts for the SOC dashboard widget."""
    return {
        "open": (
            db.query(Alert)
            .filter(
                Alert.user_id == user_id,
                Alert.status == ALERT_STATUS_OPEN,
            )
            .count()
        ),
        "acknowledged": (
            db.query(Alert)
            .filter(
                Alert.user_id == user_id,
                Alert.status == ALERT_STATUS_ACKNOWLEDGED,
            )
            .count()
        ),
        "critical": (
            db.query(Alert)
            .filter(
                Alert.user_id == user_id,
                Alert.severity == "CRITICAL",
                Alert.status == ALERT_STATUS_OPEN,
            )
            .count()
        ),
    }