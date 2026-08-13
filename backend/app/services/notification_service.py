from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.logger import logger
from app.models.finding import Finding
from app.models.notification import Notification
from app.models.scan import Scan
from app.models.user import User
from app.ws.hub import scan_event_hub

_NOTIFICATION_TYPES = {
    "critical_finding",
    "assignment",
}


def _publish_notification_event(notification: Notification) -> None:
    scan_event_hub.publish(
        {
            "type": "notification.created",
            "notification_id": notification.id,
            "user_id": notification.user_id,
        }
    )


def create_notification(
    db: Session,
    *,
    user_id: int,
    notification_type: str,
    title: str,
    body: str | None = None,
    severity: str | None = None,
    finding_id: int | None = None,
) -> Notification:
    """
    Persist a notification and push a realtime event to the target user.
    """

    if notification_type not in _NOTIFICATION_TYPES:
        notification_type = "generic"

    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        body=body,
        severity=severity,
        finding_id=finding_id,
    )

    db.add(notification)
    db.flush()

    _publish_notification_event(notification)

    return notification


def notify_scan_critical_findings(
    db: Session,
    scan: Scan,
    asset_owner_id: int,
    critical_findings: list[Finding],
) -> None:
    """
    Notify the asset owner about critical/high findings from a scan.

    Aggregates into a single notification per scan to avoid alert spam.
    """

    if not critical_findings:
        return

    high_count = sum(
        1
        for finding in critical_findings
        if finding.severity == "HIGH"
    )
    critical_count = len(critical_findings) - high_count

    top = critical_findings[0]
    first_cve = top.cve or top.title

    create_notification(
        db,
        user_id=asset_owner_id,
        notification_type="critical_finding",
        title=f"Critical finding: {first_cve}",
        body=(
            f"Scan #{scan.id} on your asset found "
            f"{critical_count} critical and {high_count} high "
            f"severity vulnerabilities."
        ),
        severity="CRITICAL",
        finding_id=top.id,
    )

    logger.info(
        "Notified user %s of %d critical/high findings from scan %s",
        asset_owner_id,
        len(critical_findings),
        scan.id,
    )


def notify_finding_assignment(
    db: Session,
    finding: Finding,
    assignee_id: int,
    assigned_by: User,
) -> None:
    """
    Notify a user that a finding was assigned to them.
    """

    create_notification(
        db,
        user_id=assignee_id,
        notification_type="assignment",
        title=f"Finding assigned to you",
        body=(
            f"{assigned_by.username} assigned "
            f"{finding.cve or finding.title} to you."
        ),
        severity=finding.severity,
        finding_id=finding.id,
    )


def list_notifications(
    db: Session,
    user_id: int,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Return a user's notifications, most recent first.
    """

    rows = (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
        )
        .order_by(
            Notification.created_at.desc(),
            Notification.id.desc(),
        )
        .limit(limit)
        .all()
    )

    total = (
        db.query(func.count(Notification.id))
        .filter(
            Notification.user_id == user_id,
        )
        .scalar()
        or 0
    )

    unread = (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
        )
        .count()
    )

    return {
        "items": rows,
        "total": total,
        "unread": unread,
    }


def unread_notification_count(
    db: Session,
    user_id: int,
) -> int:
    return (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
        )
        .count()
    )


def mark_notification_read(
    db: Session,
    notification_id: int,
    user_id: int,
) -> Notification | None:
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        .first()
    )

    if notification is None:
        return None

    if notification.read_at is None:
        notification.read_at = datetime.now(UTC)

    db.commit()
    db.refresh(notification)

    return notification


def mark_all_notifications_read(
    db: Session,
    user_id: int,
) -> int:
    result = (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
        )
        .update(
            {
                "read_at": datetime.now(UTC),
            }
        )
    )

    db.commit()

    return result
