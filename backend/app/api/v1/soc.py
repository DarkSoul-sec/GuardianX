from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.auth import verify_access_token
from app.database.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.alert import (
    AlertListResponse,
    AlertResponse,
    AlertStatusUpdate,
    AlertSummaryResponse,
    IncidentCreate,
    IncidentListResponse,
    IncidentResponse,
    IncidentUpdate,
)
from app.services.alert_service import (
    alert_summary,
    create_incident,
    delete_incident,
    get_alert,
    get_incident,
    list_alerts,
    list_incidents,
    update_alert_status,
    update_incident,
)
from app.services.soc_service import get_soc_overview, get_scan_health
from app.ws.hub import scan_event_hub

router = APIRouter(
    prefix="/soc",
    tags=["SOC"],
)


@router.get(
    "/overview",
)
def get_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_soc_overview(
        db,
        current_user,
    )


@router.get(
    "/scans/health",
)
def get_scan_health_endpoint(
    days: int = Query(14, ge=1, le=60),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_scan_health(
        db,
        current_user,
        days=days,
    )


@router.get(
    "/alerts",
    response_model=AlertListResponse,
)
def get_alerts(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: str | None = Query(None),
    severity: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_alerts(
        db,
        current_user.id,
        limit=limit,
        offset=offset,
        status=status,
        severity=severity,
    )


@router.get(
    "/alerts/summary",
    response_model=AlertSummaryResponse,
)
def get_alert_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return alert_summary(db, current_user.id)


@router.patch(
    "/alerts/{alert_id}",
    response_model=AlertResponse,
)
def patch_alert(
    alert_id: int,
    payload: AlertStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = get_alert(db, alert_id, current_user.id)

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail="Alert not found.",
        )

    return update_alert_status(
        db,
        alert,
        payload.status,
    )


@router.get(
    "/incidents",
    response_model=IncidentListResponse,
)
def get_incidents(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: str | None = Query(None),
    severity: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_incidents(
        db,
        current_user.id,
        limit=limit,
        offset=offset,
        status=status,
        severity=severity,
    )


@router.post(
    "/incidents",
    response_model=IncidentResponse,
    status_code=201,
)
def post_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_incident(
        db,
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        status=payload.status,
        asset_id=payload.asset_id,
        alert_id=payload.alert_id,
        finding_id=payload.finding_id,
        assignee_id=payload.assignee_id,
    )


@router.get(
    "/incidents/{incident_id}",
    response_model=IncidentResponse,
)
def get_single_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    incident = get_incident(db, incident_id, current_user.id)

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found.",
        )

    return incident


@router.patch(
    "/incidents/{incident_id}",
    response_model=IncidentResponse,
)
def patch_incident(
    incident_id: int,
    payload: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    incident = get_incident(db, incident_id, current_user.id)

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found.",
        )

    return update_incident(
        db,
        incident,
        status=payload.status,
        assignee_id=payload.assignee_id,
        summary=payload.summary,
        actor=current_user,
    )


@router.delete(
    "/incidents/{incident_id}",
    status_code=204,
)
def remove_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    incident = get_incident(db, incident_id, current_user.id)

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found.",
        )

    delete_incident(db, incident)
    return None


@router.websocket("/alerts/ws")
async def alert_events_ws(websocket: WebSocket):
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
        event_types={"alert.created"},
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