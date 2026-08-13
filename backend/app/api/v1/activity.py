from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.auth import verify_access_token
from app.database.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.logger import logger
from app.models.user import User
from app.schemas.activity import (
    ActivityListResponse,
)
from app.services.activity_service import (
    list_activities,
    recent_login_history,
)
from app.ws.hub import scan_event_hub

router = APIRouter(
    prefix="/activity",
    tags=["Activity"],
)


@router.get(
    "",
    response_model=ActivityListResponse,
)
def get_activity(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Activity feed requested for user %s", current_user.id)

    return list_activities(
        db,
        current_user.id,
        limit=limit,
    )


@router.get(
    "/logins",
    response_model=ActivityListResponse,
)
def get_login_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = recent_login_history(
        db,
        current_user.id,
        limit=limit,
    )

    return {
        "items": rows,
        "total": len(rows),
    }


@router.websocket("/ws")
async def activity_events_ws(websocket: WebSocket):
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
        event_types={"activity.created"},
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