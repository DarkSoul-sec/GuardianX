from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog
from app.ws.hub import scan_event_hub

_ACTIVITIES = {
    "login",
    "logout",
    "asset_created",
    "asset_updated",
    "asset_deleted",
    "scan_started",
    "scan_completed",
    "scan_failed",
    "scan_cancelled",
    "finding_opened",
    "finding_closed",
    "finding_assigned",
    "threat_search",
    "vt_lookup",
    "intelligence_search",
    "config_updated",
    "user_created",
    "role_changed",
}


def record_activity(
    db: Session,
    *,
    user_id: int,
    action: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    detail: str | None = None,
    meta: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> ActivityLog:
    """
    Persist an audit event and push a realtime `activity.created` event.

    Unknown action names are stored verbatim; the whitelist above is used
    for editorial/validation purposes by callers and documentation.
    """

    entry = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=detail,
        meta=meta,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.add(entry)
    db.flush()

    scan_event_hub.publish(
        {
            "type": "activity.created",
            "activity_id": entry.id,
            "action": entry.action,
            "user_id": entry.user_id,
        }
    )

    return entry


def list_activities(
    db: Session,
    user_id: int,
    *,
    limit: int = 50,
    actions: list[str] | None = None,
) -> dict:
    """Feed a user's activity timeline, most recent first."""
    query = db.query(ActivityLog).filter(
        ActivityLog.user_id == user_id,
    )

    if actions:
        query = query.filter(ActivityLog.action.in_(actions))

    rows = (
        query.order_by(
            ActivityLog.created_at.desc(),
            ActivityLog.id.desc(),
        )
        .limit(limit)
        .all()
    )

    total = (
        db.query(func.count(ActivityLog.id))
        .filter(ActivityLog.user_id == user_id)
        .scalar()
        or 0
    )

    return {
        "items": rows,
        "total": total,
    }


def recent_login_history(
    db: Session,
    user_id: int,
    *,
    limit: int = 20,
) -> list[ActivityLog]:
    """Return the most recent successful logins for a user."""
    return (
        db.query(ActivityLog)
        .filter(
            ActivityLog.user_id == user_id,
            ActivityLog.action == "login",
        )
        .order_by(
            ActivityLog.created_at.desc(),
            ActivityLog.id.desc(),
        )
        .limit(limit)
        .all()
    )