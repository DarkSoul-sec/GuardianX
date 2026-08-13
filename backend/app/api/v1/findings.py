from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, WebSocket, WebSocketDisconnect
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.auth import verify_access_token
from app.database.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.logger import logger
from app.models.user import User
from app.schemas.finding import (
    AssigneeResponse,
    BulkFindingsStatusUpdate,
    BulkUpdateResponse,
    FindingActivityResponse,
    FindingDetailResponse,
    FindingIntelligenceResponse,
    FindingListResponse,
    FindingStatsResponse,
    FindingStatus,
    FindingStatusUpdate,
    FindingTriageUpdate,
)
from app.services.finding_service import (
    bulk_update_findings_status,
    export_findings_csv,
    get_finding,
    get_finding_activities,
    get_findings,
    get_findings_stats,
    list_findings_assignees,
    update_finding_status,
    update_finding_triage,
)
from app.ws.hub import scan_event_hub
from app.tasks.intelligence_worker import get_or_schedule

router = APIRouter(
    prefix="/findings",
    tags=["Findings"],
)


@router.get(
    "",
    response_model=FindingListResponse,
)
def list_findings(
    severity: str | None = Query(default=None),
    status: FindingStatus | None = Query(default=None),
    asset: str | None = Query(default=None),
    scan: int | None = Query(default=None, alias="scan"),
    cve: str | None = Query(default=None),
    search: str | None = Query(default=None),
    assigned: Literal["me", "unassigned"] | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    sort_by: Literal["created_at", "severity", "title", "cve", "status", "asset"] = Query(default="created_at"),
    sort_order: Literal["asc", "desc"] = Query(default="desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Finding list requested")

    return get_findings(
        db=db,
        current_user=current_user,
        severity=severity,
        status=status.value if status else None,
        asset=asset,
        scan=scan,
        cve=cve,
        search=search,
        assigned=assigned,
        page=page,
        size=size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get(
    "/assignees",
    response_model=list[AssigneeResponse],
)
def finding_assignees(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    logger.info("Finding assignee list requested")
    return list_findings_assignees(db)


@router.get(
    "/stats",
    response_model=FindingStatsResponse,
)
def finding_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Finding stats requested")

    return get_findings_stats(
        db,
        current_user,
    )


@router.get(
    "/export",
    response_class=Response,
)
def export_findings(
    severity: str | None = Query(default=None),
    status: FindingStatus | None = Query(default=None),
    asset: str | None = Query(default=None),
    scan: int | None = Query(default=None, alias="scan"),
    cve: str | None = Query(default=None),
    search: str | None = Query(default=None),
    assigned: Literal["me", "unassigned"] | None = Query(default=None),
    sort_by: Literal["created_at", "severity", "title", "cve", "status", "asset"] = Query(default="created_at"),
    sort_order: Literal["asc", "desc"] = Query(default="desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Finding CSV export requested")

    csv_content = export_findings_csv(
        db=db,
        current_user=current_user,
        severity=severity,
        status=status.value if status else None,
        asset=asset,
        scan=scan,
        cve=cve,
        search=search,
        assigned=assigned,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    filename = f"guardianx-findings-{current_user.username}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.post(
    "/bulk-status",
    response_model=BulkUpdateResponse,
)
def bulk_change_status(
    payload: BulkFindingsStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Bulk finding status change requested: %s findings", len(payload.ids))

    return bulk_update_findings_status(
        db,
        payload.ids,
        payload.status.value,
        current_user,
    )


@router.get(
    "/{finding_id}",
    response_model=FindingDetailResponse,
)
def retrieve_finding(
    finding_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Finding viewed: %s", finding_id)

    finding = get_finding(db, finding_id, current_user)

    if finding is None:
        raise HTTPException(
            status_code=404,
            detail="Finding not found.",
        )

    return finding


@router.get(
    "/{finding_id}/intelligence",
    response_model=FindingIntelligenceResponse,
    summary="Get non-blocking external vulnerability enrichment",
)
def finding_intelligence(
    finding_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Schedule external CVE enrichment without delaying the Findings view."""
    finding = get_finding(db, finding_id, current_user)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found.")
    if not finding["cve"]:
        return {"status": "not_available", "intelligence": None}
    status, intelligence = get_or_schedule(finding["cve"])
    return {"status": status, "intelligence": intelligence}


@router.get(
    "/{finding_id}/activities",
    response_model=list[FindingActivityResponse],
)
def finding_activities(
    finding_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Finding activities viewed: %s", finding_id)

    activities = get_finding_activities(
        db,
        finding_id,
        current_user,
    )

    if activities is None:
        raise HTTPException(
            status_code=404,
            detail="Finding not found.",
        )

    return activities


@router.patch(
    "/{finding_id}/status",
    response_model=FindingDetailResponse,
)
def change_status(
    finding_id: int,
    payload: FindingStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Finding updated: %s", finding_id)

    finding = update_finding_status(
        db,
        finding_id,
        payload.status.value,
        current_user,
    )

    if finding is None:
        raise HTTPException(
            status_code=404,
            detail="Finding not found.",
        )

    return finding


@router.patch(
    "/{finding_id}/triage",
    response_model=FindingDetailResponse,
)
def change_triage(
    finding_id: int,
    payload: FindingTriageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Finding triage update: %s", finding_id)

    fields = payload.model_dump(exclude_unset=True)

    finding = update_finding_triage(
        db,
        finding_id,
        current_user,
        **{
            key: value
            for key, value in fields.items()
            if key in {"status", "assignee_id", "notes", "due_date"}
        },
    )

    if finding is None:
        raise HTTPException(
            status_code=404,
            detail="Finding not found.",
        )

    return finding


@router.websocket("/ws")
async def finding_events_ws(websocket: WebSocket):
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
        event_types={"finding.updated"},
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
