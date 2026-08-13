import threading
from datetime import UTC, datetime, timedelta

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.roles import UserRole

_DASHBOARD_CACHE_TTL = timedelta(seconds=30)
_dashboard_cache: dict[int, tuple[datetime, dict]] = {}
_dashboard_cache_lock = threading.Lock()
from app.core.scan_status import ScanStatus
from app.logger import logger
from app.models.asset import Asset
from app.models.finding import Finding
from app.models.scan import Scan
from app.models.scan_result import ScanResult
from app.models.user import User
from app.services.risk_service import calculate_risk_score


# ---------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------


def _scope_to_visible_assets(query, current_user: User):
    """
    Restrict a query to assets visible to the requesting user.
    """

    if current_user.role != UserRole.ADMIN:
        query = query.filter(
            Asset.created_by == current_user.id,
        )

    return query


def _get_assets_count(
    db: Session,
    current_user: User,
) -> int:
    return (
        _scope_to_visible_assets(
            db.query(func.count(Asset.id)),
            current_user,
        ).scalar()
        or 0
    )


def _get_scan_count(
    db: Session,
    current_user: User,
    status: ScanStatus | None = None,
) -> int:

    query = _scope_to_visible_assets(
        db.query(func.count(Scan.id)).join(Asset),
        current_user,
    )

    if status is not None:
        query = query.filter(
            Scan.status == status,
        )

    return query.scalar() or 0


def _get_open_ports(
    db: Session,
    current_user: User,
) -> int:

    return (
        _scope_to_visible_assets(
            db.query(func.count(ScanResult.id))
            .join(Scan)
            .join(Asset),
            current_user,
        ).scalar()
        or 0
    )


def _get_last_scan(
    db: Session,
    current_user: User,
):

    return _scope_to_visible_assets(
        db.query(func.max(Scan.created_at)).join(Asset),
        current_user,
    ).scalar()


# ---------------------------------------------------------------------
# Legacy Dashboard
# ---------------------------------------------------------------------


def get_dashboard(
    db: Session,
    current_user: User,
) -> dict:
    """
    Legacy dashboard endpoint.
    """

    return {
        "total_assets": _get_assets_count(db, current_user),
        "total_scans": _get_scan_count(db, current_user),
        "pending_scans": _get_scan_count(
            db,
            current_user,
            ScanStatus.PENDING,
        ),
        "running_scans": _get_scan_count(
            db,
            current_user,
            ScanStatus.RUNNING,
        ),
        "completed_scans": _get_scan_count(
            db,
            current_user,
            ScanStatus.COMPLETED,
        ),
        "failed_scans": _get_scan_count(
            db,
            current_user,
            ScanStatus.FAILED,
        ),
        "open_ports": _get_open_ports(
            db,
            current_user,
        ),
        "last_scan": _get_last_scan(
            db,
            current_user,
        ),
    }
def _get_open_ports_count(
    db: Session,
    current_user: User,
) -> int:
    """
    Count unique exposed open ports across visible assets.
    """

    return (
        _scope_to_visible_assets(
            db.query(func.count(ScanResult.id))
            .join(
                Scan,
                ScanResult.scan_id == Scan.id,
            )
            .join(
                Asset,
                Scan.asset_id == Asset.id,
            )
            .filter(
                ScanResult.state == "open",
            ),
            current_user,
        ).scalar()
        or 0
    )


def _get_services_count(
    db: Session,
    current_user: User,
) -> int:
    """
    Count running services detected across visible assets.
    """

    return (
        _scope_to_visible_assets(
            db.query(func.count(ScanResult.id))
            .join(
                Scan,
                ScanResult.scan_id == Scan.id,
            )
            .join(
                Asset,
                Scan.asset_id == Asset.id,
            ),
            current_user,
        ).scalar()
        or 0
    )


def _get_risk_trend(
    db: Session,
    current_user: User,
    days: int = 14,
) -> list[dict]:
    """
    Build a daily risk score trend from real finding history.

    Days without findings resolve to a score of zero, so the chart
    always covers a contiguous window.
    """

    cutoff = datetime.now(UTC) - timedelta(days=days - 1)

    query = (
        db.query(
            func.date(Finding.created_at).label("day"),
            func.sum(
                case(
                    (Finding.severity == "CRITICAL", 1),
                    else_=0,
                )
            ).label("critical"),
            func.sum(
                case(
                    (Finding.severity == "HIGH", 1),
                    else_=0,
                )
            ).label("high"),
            func.sum(
                case(
                    (Finding.severity == "MEDIUM", 1),
                    else_=0,
                )
            ).label("medium"),
            func.sum(
                case(
                    (Finding.severity == "LOW", 1),
                    else_=0,
                )
            ).label("low"),
        )
        .select_from(Finding)
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
        .filter(
            Finding.created_at >= cutoff,
        )
        .group_by(
            func.date(Finding.created_at),
        )
    )

    rows = _scope_to_visible_assets(
        query,
        current_user,
    ).all()

    by_day = {}

    for row in rows:
        by_day[str(row.day)] = calculate_risk_score(
            critical=row.critical or 0,
            high=row.high or 0,
            medium=row.medium or 0,
            low=row.low or 0,
        )

    trend = []

    for index in range(days):
        day = (cutoff + timedelta(days=index)).date()
        trend.append(
            {
                "date": day.isoformat(),
                "score": by_day.get(day.isoformat(), 0),
            }
        )

    return trend


def _get_asset_growth(
    db: Session,
    current_user: User,
    days: int = 14,
) -> list[dict]:
    """
    Build a cumulative asset growth series over the given window.

    Assets created before the window are used as the baseline so the
    cumulative count is accurate from day one.
    """

    cutoff = datetime.now(UTC) - timedelta(days=days - 1)

    base = (
        _scope_to_visible_assets(
            db.query(func.count(Asset.id)).filter(
                Asset.created_at < cutoff,
            ),
            current_user,
        ).scalar()
        or 0
    )

    rows = (
        _scope_to_visible_assets(
            db.query(
                func.date(Asset.created_at).label("day"),
                func.count(Asset.id).label("count"),
            )
            .filter(
                Asset.created_at >= cutoff,
            )
            .group_by(
                func.date(Asset.created_at),
            ),
            current_user,
        ).all()
    )

    by_day = {
        str(row.day): row.count
        for row in rows
    }

    growth = []
    running = base

    for index in range(days):
        day = (cutoff + timedelta(days=index)).date()
        running += by_day.get(day.isoformat(), 0)
        growth.append(
            {
                "date": day.isoformat(),
                "count": running,
            }
        )

    return growth


# ---------------------------------------------------------------------
# Dashboard Overview Helpers
# ---------------------------------------------------------------------


def _get_severity_summary(
    db: Session,
    current_user: User,
) -> dict:

    query = (
        db.query(
            func.sum(
                case(
                    (Finding.severity == "CRITICAL", 1),
                    else_=0,
                )
            ).label("critical"),
            func.sum(
                case(
                    (Finding.severity == "HIGH", 1),
                    else_=0,
                )
            ).label("high"),
            func.sum(
                case(
                    (Finding.severity == "MEDIUM", 1),
                    else_=0,
                )
            ).label("medium"),
            func.sum(
                case(
                    (Finding.severity == "LOW", 1),
                    else_=0,
                )
            ).label("low"),
            func.count(Finding.id).label("total"),
        )
        .select_from(Finding)
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
    )

    row = _scope_to_visible_assets(
        query,
        current_user,
    ).first()

    return {
        "critical": row.critical or 0,
        "high": row.high or 0,
        "medium": row.medium or 0,
        "low": row.low or 0,
        "total": row.total or 0,
    }


def _get_recent_scans(
    db: Session,
    current_user: User,
):

    finding_counts = (
        db.query(
            ScanResult.scan_id.label("scan_id"),
            func.count(Finding.id).label("total"),
        )
        .join(
            Finding,
            Finding.scan_result_id == ScanResult.id,
            isouter=True,
        )
        .group_by(
            ScanResult.scan_id,
        )
        .subquery()
    )

    query = (
        db.query(
            Scan.id.label("scan_id"),
            Asset.name.label("asset_name"),
            Scan.status,
            Scan.started_at,
            Scan.finished_at,
            func.coalesce(
                finding_counts.c.total,
                0,
            ).label("finding_count"),
        )
        .join(
            Asset,
            Scan.asset_id == Asset.id,
        )
        .outerjoin(
            finding_counts,
            finding_counts.c.scan_id == Scan.id,
        )
    )

    return (
        _scope_to_visible_assets(
            query,
            current_user,
        )
        .order_by(
            Scan.started_at.desc().nullslast(),
            Scan.created_at.desc(),
        )
        .limit(5)
        .all()
    )


def _get_recent_findings(
    db: Session,
    current_user: User,
):

    query = (
        db.query(
            Finding.cve,
            Finding.title,
            Finding.severity,
            Finding.status,
            Finding.created_at,
            Asset.name.label("asset"),
        )
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
    )

    return (
        _scope_to_visible_assets(
            query,
            current_user,
        )
        .order_by(
            Finding.created_at.desc(),
        )
        .limit(5)
        .all()
    )


def _get_top_vulnerable_assets(
    db: Session,
    current_user: User,
):

    query = (
        db.query(
            Scan.asset_id.label("asset_id"),
            Asset.name.label("asset_name"),
            func.count(Finding.id).label("total_findings"),
            func.sum(
                case(
                    (Finding.severity == "CRITICAL", 1),
                    else_=0,
                )
            ).label("critical"),
            func.sum(
                case(
                    (Finding.severity == "HIGH", 1),
                    else_=0,
                )
            ).label("high"),
            func.sum(
                case(
                    (Finding.severity == "MEDIUM", 1),
                    else_=0,
                )
            ).label("medium"),
            func.sum(
                case(
                    (Finding.severity == "LOW", 1),
                    else_=0,
                )
            ).label("low"),
        )
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
        .group_by(
            Scan.asset_id,
            Asset.name,
        )
    )

    rows = (
        _scope_to_visible_assets(
            query,
            current_user,
        )
        .order_by(
            func.count(Finding.id).desc(),
            func.sum(
                case(
                    (Finding.severity == "CRITICAL", 1),
                    else_=0,
                )
            ).desc(),
        )
        .limit(5)
        .all()
    )

    assets = []

    for row in rows:
        assets.append(
            {
                "asset_id": row.asset_id,
                "asset_name": row.asset_name,
                "risk_score": calculate_risk_score(
                    critical=row.critical or 0,
                    high=row.high or 0,
                    medium=row.medium or 0,
                    low=row.low or 0,
                ),
                "total_findings": row.total_findings or 0,
                "critical_findings": row.critical or 0,
            }
        )

    return assets


def _get_asset_distribution(
    db: Session,
    current_user: User,
) -> list[dict]:
    """
    Count assets grouped by type, ordered most common first.
    """

    rows = (
        _scope_to_visible_assets(
            db.query(
                Asset.asset_type.label("type"),
                func.count(Asset.id).label("count"),
            ),
            current_user,
        )
        .group_by(
            Asset.asset_type,
        )
        .order_by(
            func.count(Asset.id).desc(),
        )
        .all()
    )

    return [
        {
            "type": row.type.value if hasattr(row.type, "value") else str(row.type),
            "count": row.count,
        }
        for row in rows
    ]


def _get_findings_trend(
    db: Session,
    current_user: User,
    days: int = 14,
) -> list[dict]:
    """
    Build a daily finding-count series split by severity.

    Days without findings resolve to zero counts so the chart always
    covers a contiguous window.
    """

    cutoff = datetime.now(UTC) - timedelta(days=days - 1)

    query = (
        db.query(
            func.date(Finding.created_at).label("day"),
            func.sum(
                case(
                    (Finding.severity == "CRITICAL", 1),
                    else_=0,
                )
            ).label("critical"),
            func.sum(
                case(
                    (Finding.severity == "HIGH", 1),
                    else_=0,
                )
            ).label("high"),
            func.sum(
                case(
                    (Finding.severity == "MEDIUM", 1),
                    else_=0,
                )
            ).label("medium"),
            func.sum(
                case(
                    (Finding.severity == "LOW", 1),
                    else_=0,
                )
            ).label("low"),
        )
        .select_from(Finding)
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
        .filter(
            Finding.created_at >= cutoff,
        )
        .group_by(
            func.date(Finding.created_at),
        )
    )

    rows = _scope_to_visible_assets(
        query,
        current_user,
    ).all()

    by_day = {}

    for row in rows:
        by_day[str(row.day)] = {
            "critical": row.critical or 0,
            "high": row.high or 0,
            "medium": row.medium or 0,
            "low": row.low or 0,
        }

    trend = []

    for index in range(days):
        day = (cutoff + timedelta(days=index)).date()
        counts = by_day.get(
            day.isoformat(),
            {"critical": 0, "high": 0, "medium": 0, "low": 0},
        )
        trend.append(
            {
                "date": day.isoformat(),
                **counts,
            }
        )

    return trend


def _get_top_vulnerabilities(
    db: Session,
    current_user: User,
    limit: int = 5,
) -> list[dict]:
    """
    Return the highest-CVSS findings across the visible estate.
    """

    query = (
        db.query(
            Finding.cve,
            Finding.title,
            Finding.severity,
            Finding.cvss,
            Finding.status,
            Asset.name.label("asset"),
        )
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
    )

    rows = (
        _scope_to_visible_assets(
            query,
            current_user,
        )
        .order_by(
            Finding.cvss.desc().nullslast(),
            Finding.created_at.desc(),
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "cve": row.cve,
            "title": row.title,
            "severity": row.severity,
            "cvss": row.cvss,
            "status": row.status,
            "asset": row.asset,
        }
        for row in rows
    ]


# ---------------------------------------------------------------------
# Professional Dashboard
# ---------------------------------------------------------------------


def get_dashboard_overview(
    db: Session,
    current_user: User,
) -> dict:
    """
    Build the professional GuardianX dashboard.

    The dashboard is composed using helper methods to keep this function
    small, readable, and easy to maintain.
    """

    logger.info(
        "Dashboard requested by user %s",
        current_user.id,
    )

    now = datetime.now(UTC)

    with _dashboard_cache_lock:
        cached = _dashboard_cache.get(current_user.id)

    if cached is not None and now - cached[0] < _DASHBOARD_CACHE_TTL:
        return cached[1]

    severity = _get_severity_summary(
        db,
        current_user,
    )

    risk_score = calculate_risk_score(
        critical=severity["critical"],
        high=severity["high"],
        medium=severity["medium"],
        low=severity["low"],
    )

    recent_scans = _get_recent_scans(
        db,
        current_user,
    )

    recent_findings = _get_recent_findings(
        db,
        current_user,
    )

    top_assets = _get_top_vulnerable_assets(
        db,
        current_user,
    )

    risk_trend = _get_risk_trend(
        db,
        current_user,
    )

    asset_growth = _get_asset_growth(
        db,
        current_user,
    )

    asset_distribution = _get_asset_distribution(
        db,
        current_user,
    )

    findings_trend = _get_findings_trend(
        db,
        current_user,
    )

    top_vulnerabilities = _get_top_vulnerabilities(
        db,
        current_user,
    )

    response = {
        "assets": _get_assets_count(
            db,
            current_user,
        ),
        "completed_scans": _get_scan_count(
            db,
            current_user,
            ScanStatus.COMPLETED,
        ),
        "open_ports": _get_open_ports_count(
            db,
            current_user,
        ),
        "total_services": _get_services_count(
            db,
            current_user,
        ),
        "critical_findings": severity["critical"],
        "high_findings": severity["high"],
        "medium_findings": severity["medium"],
        "low_findings": severity["low"],
        "total_findings": severity["total"],
        "risk_score": risk_score,
        "risk_trend": risk_trend,
        "asset_growth": asset_growth,
        "asset_distribution": asset_distribution,
        "findings_trend": findings_trend,
        "top_vulnerabilities": top_vulnerabilities,
        "recent_scans": [
            {
                "scan_id": scan.scan_id,
                "asset_name": scan.asset_name,
                "status": (
                    scan.status.value
                    if hasattr(scan.status, "value")
                    else scan.status
                ),
                "started_at": scan.started_at,
                "finished_at": scan.finished_at,
                "finding_count": scan.finding_count,
            }
            for scan in recent_scans
        ],
        "top_vulnerable_assets": top_assets,
        "recent_findings": [
            {
                "cve": finding.cve,
                "title": finding.title,
                "severity": finding.severity,
                "asset": finding.asset,
                "created_at": finding.created_at,
                "status": finding.status,
            }
            for finding in recent_findings
        ],
    }

    logger.info(
        "Dashboard generated successfully for user %s",
        current_user.id,
    )

    with _dashboard_cache_lock:
        _dashboard_cache[current_user.id] = (now, response)

    return response
