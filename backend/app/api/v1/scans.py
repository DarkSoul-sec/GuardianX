from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.auth import verify_access_token
from app.database.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.scan import (
    ScanCreate,
    ScanOperationsResponse,
    ScanResponse,
    ScanResultResponse,
)
from app.services.scan_service import (
    cancel_scan,
    create_scan,
    get_asset_for_scan,
    get_scan,
    get_scan_operations,
    get_scans,
    get_scan_results,
)
from app.ws.hub import scan_event_hub

router = APIRouter(
    prefix="/scans",
    tags=["Scans"],
)


@router.post(
    "",
    response_model=ScanResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_scan(
    request: ScanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    asset = get_asset_for_scan(db, request.asset_id, current_user)

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found.",
        )

    return create_scan(db, asset, request.scan_profile)


@router.get(
    "",
    response_model=list[ScanResponse],
)
def list_scans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_scans(db, current_user)


@router.get(
    "/operations",
    response_model=ScanOperationsResponse,
)
def scan_operations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_scan_operations(db, current_user)


@router.get(
    "/{scan_id}",
    response_model=ScanResponse,
)
def retrieve_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scan = get_scan(db, scan_id, current_user)

    if scan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found.",
        )

    return scan


@router.get(
    "/{scan_id}/results",
    response_model=list[ScanResultResponse],
)
def retrieve_scan_results(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scan = get_scan(db, scan_id, current_user)

    if scan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found.",
        )

    return get_scan_results(db, scan_id, current_user)


@router.post(
    "/{scan_id}/cancel",
    response_model=ScanResponse,
)
def cancel_scan_route(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scan = cancel_scan(db, scan_id, current_user)

    if scan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found.",
        )

    return get_scan(db, scan_id, current_user)


@router.websocket("/ws")
async def scan_events_ws(websocket: WebSocket):
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
        event_types={"scan.updated"},
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
