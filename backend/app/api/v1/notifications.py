from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.auth import verify_access_token
from app.database.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.logger import logger
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from app.services.notification_service import (
    list_notifications,
    mark_all_notifications_read,
    mark_notification_read,
    unread_notification_count,
)
from app.ws.hub import scan_event_hub

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get(
    "",
    response_model=NotificationListResponse,
)
def get_notifications(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Notification list requested for user %s", current_user.id)

    return list_notifications(
        db,
        current_user.id,
        limit=limit,
    )


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
)
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {
        "unread": unread_notification_count(
            db,
            current_user.id,
        ),
    }


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
def read_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = mark_notification_read(
        db,
        notification_id,
        current_user.id,
    )

    if notification is None:
        raise HTTPException(
            status_code=404,
            detail="Notification not found.",
        )

    return notification


@router.post(
    "/read-all",
    response_model=UnreadCountResponse,
)
def read_all_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = mark_all_notifications_read(
        db,
        current_user.id,
    )

    logger.info("Marked %s notifications read for user %s", count, current_user.id)

    return {
        "unread": 0,
    }


@router.websocket("/ws")
async def notification_events_ws(websocket: WebSocket):
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=4401)
        return

    try:
        payload = verify_access_token(token)
    except InvalidTokenError:
        await websocket.close(code=4401)
        return

    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        await websocket.close(code=4401)
        return

    await websocket.accept()

    subscriber_id, queue = scan_event_hub.subscribe(
        event_types={"notification.created"},
    )

    try:
        while True:
            event = await queue.get()

            if event.get("user_id") != user_id:
                continue

            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        scan_event_hub.unsubscribe(subscriber_id)
