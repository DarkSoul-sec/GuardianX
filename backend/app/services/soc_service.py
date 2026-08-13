from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.roles import UserRole
from app.core.scan_status import ScanStatus
from app.models.activity_log import ActivityLog
from app.models.alert import Alert
from app.models.asset import Asset
from app.models.incident import Incident
from app.models.scan import Scan
from app.models.scan_result import ScanResult
from app.models.user import User


def _scope(query, current_user: User):
    if current_user.role != UserRole.ADMIN:
        return query.filter(Asset.created_by == current_user.id)
    return query


def _user_scope(query, current_user: User):
    return query.filter(ActivityLog.user_id == current_user.id)


def get_soc_overview(
    db: Session,
    current_user: User,
) -> dict[str, Any]:
    """Comprehensive SOC operational snapshot for the dashboard."""

    # ---- Scan reliability -------------------------------------------------
    total_scans = (
        _scope(db.query(func.count(Scan.id)).join(Asset), current_user).scalar() or 0
    )
    completed_scans = (
        _scope(
            db.query(func.count(Scan.id))
            .join(Asset)
            .filter(Scan.status == ScanStatus.COMPLETED),
            current_user,
        ).scalar()
        or 0
    )
    failed_scans = (
        _scope(
            db.query(func.count(Scan.id))
            .join(Asset)
            .filter(Scan.status == ScanStatus.FAILED),
            current_user,
        ).scalar()
        or 0
    )
    cancelled_scans = (
        _scope(
            db.query(func.count(Scan.id))
            .join(Asset)
            .filter(Scan.status == ScanStatus.CANCELLED),
            current_user,
        ).scalar()
        or 0
    )
    running_scans = (
        _scope(
            db.query(func.count(Scan.id))
            .join(Asset)
            .filter(Scan.status == ScanStatus.RUNNING),
            current_user,
        ).scalar()
        or 0
    )
    pending_scans = (
        _scope(
            db.query(func.count(Scan.id))
            .join(Asset)
            .filter(Scan.status == ScanStatus.PENDING),
            current_user,
        ).scalar()
        or 0
    )

    finished = completed_scans + failed_scans + cancelled_scans
    success_rate = round(
        (completed_scans / finished) * 100, 1
    ) if finished else 0.0

    # ---- Live scans -------------------------------------------------------
    live_scans = _get_live_scans(db, current_user)

    # ---- Attack surface trend ---------------------------------------------
    attack_surface_trend = _get_attack_surface_trend(db, current_user)

    # ---- SOC entities -----------------------------------------------------
    open_alerts = (
        db.query(Alert)
        .filter(Alert.user_id == current_user.id, Alert.status == "OPEN")
        .count()
    )
    critical_alerts = (
        db.query(Alert)
        .filter(
            Alert.user_id == current_user.id,
            Alert.severity == "CRITICAL",
            Alert.status == "OPEN",
        )
        .count()
    )
    open_incidents = (
        db.query(Incident)
        .filter(
            Incident.user_id == current_user.id,
            Incident.status.in_(["OPEN", "INVESTIGATING"]),
        )
        .count()
    )
    total_incidents = (
        db.query(Incident)
        .filter(Incident.user_id == current_user.id)
        .count()
    )

    # ---- Timeline ---------------------------------------------------------
    recent_activity = _get_recent_activity(db, current_user)

    return {
        "scans": {
            "total": total_scans,
            "completed": completed_scans,
            "failed": failed_scans,
            "cancelled": cancelled_scans,
            "running": running_scans,
            "pending": pending_scans,
            "success_rate": success_rate,
        },
        "live_scans": live_scans,
        "attack_surface_trend": attack_surface_trend,
        "alerts": {
            "open": open_alerts,
            "critical": critical_alerts,
        },
        "incidents": {
            "open": open_incidents,
            "total": total_incidents,
        },
        "recent_activity": recent_activity,
    }


def _get_live_scans(
    db: Session,
    current_user: User,
) -> list[dict[str, Any]]:
    rows = (
        _scope(
            db.query(
                Scan.id.label("scan_id"),
                Scan.status,
                Scan.started_at,
                Asset.name.label("asset_name"),
            )
            .join(Asset)
            .filter(Scan.status.in_([ScanStatus.RUNNING, ScanStatus.PENDING])),
            current_user,
        )
        .order_by(Scan.started_at.desc().nullslast())
        .limit(20)
        .all()
    )

    now = datetime.now(UTC)

    result = []
    for row in rows:
        elapsed = None
        if row.started_at is not None:
            elapsed = max(0, int((now - row.started_at).total_seconds()))

        result.append(
            {
                "scan_id": row.scan_id,
                "asset_name": row.asset_name,
                "status": (
                    row.status.value if hasattr(row.status, "value") else str(row.status)
                ),
                "started_at": row.started_at,
                "elapsed_seconds": elapsed,
            }
        )

    return result


def _get_attack_surface_trend(
    db: Session,
    current_user: User,
    days: int = 14,
) -> list[dict[str, Any]]:
    """Daily count of open ports (attack surface) across the estate."""

    cutoff = datetime.now(UTC) - timedelta(days=days - 1)

    rows = (
        _scope(
            db.query(
                func.date(Scan.created_at).label("day"),
                func.count(ScanResult.id).label("count"),
            )
            .join(Scan, ScanResult.scan_id == Scan.id)
            .join(Asset, Scan.asset_id == Asset.id)
            .filter(
                ScanResult.state == "open",
                Scan.created_at >= cutoff,
            )
            .group_by(func.date(Scan.created_at)),
            current_user,
        ).all()
    )

    by_day = {str(row.day): row.count for row in rows}

    trend = []
    for index in range(days):
        day = (cutoff + timedelta(days=index)).date()
        trend.append(
            {
                "date": day.isoformat(),
                "count": by_day.get(day.isoformat(), 0),
            }
        )

    return trend


def _get_recent_activity(
    db: Session,
    current_user: User,
    limit: int = 10,
) -> list[dict[str, Any]]:
    rows = (
        _user_scope(
            db.query(
                ActivityLog.id,
                ActivityLog.action,
                ActivityLog.detail,
                ActivityLog.entity_type,
                ActivityLog.entity_id,
                ActivityLog.ip_address,
                ActivityLog.created_at,
            ),
            current_user,
        )
        .order_by(
            ActivityLog.created_at.desc(),
            ActivityLog.id.desc(),
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "id": row.id,
            "action": row.action,
            "detail": row.detail,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "ip_address": row.ip_address,
            "created_at": row.created_at,
        }
        for row in rows
    ]


def get_scan_health(
    db: Session,
    current_user: User,
    days: int = 14,
) -> dict[str, Any]:
    """Daily scan outcomes for the SOC charts (success/fail per day)."""

    cutoff = datetime.now(UTC) - timedelta(days=days - 1)

    rows = (
        _scope(
            db.query(
                func.date(Scan.created_at).label("day"),
                func.sum(
                    case((Scan.status == ScanStatus.COMPLETED, 1), else_=0)
                ).label("completed"),
                func.sum(
                    case((Scan.status == ScanStatus.FAILED, 1), else_=0)
                ).label("failed"),
            )
            .join(Asset)
            .filter(Scan.created_at >= cutoff)
            .group_by(func.date(Scan.created_at)),
            current_user,
        ).all()
    )

    by_day = {str(row.day): {"completed": row.completed or 0, "failed": row.failed or 0} for row in rows}

    trend = []
    for index in range(days):
        day = (cutoff + timedelta(days=index)).date()
        counts = by_day.get(day.isoformat(), {"completed": 0, "failed": 0})
        trend.append(
            {
                "date": day.isoformat(),
                **counts,
            }
        )

    return {"trend": trend}