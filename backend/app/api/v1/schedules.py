from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.schedule import (
    ScheduledScanCreate,
    ScheduledScanResponse,
    ScheduledScanUpdate,
)
from app.services.schedule_service import (
    create_schedule,
    delete_schedule,
    list_schedules,
    run_schedule_now,
    update_schedule,
)

router = APIRouter(
    prefix="/schedules",
    tags=["Schedules"],
)


@router.get(
    "",
    response_model=list[ScheduledScanResponse],
)
def get_schedules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_schedules(
        db,
        current_user,
    )


@router.post(
    "",
    response_model=ScheduledScanResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_scan_schedule(
    request: ScheduledScanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_schedule(
        db,
        current_user,
        request,
    )


@router.patch(
    "/{schedule_id}",
    response_model=ScheduledScanResponse,
)
def patch_schedule(
    schedule_id: int,
    request: ScheduledScanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    schedule = update_schedule(
        db,
        schedule_id,
        current_user,
        request,
    )

    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found.",
        )

    return schedule


@router.post(
    "/{schedule_id}/run",
    response_model=ScheduledScanResponse,
)
def run_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    schedule = run_schedule_now(
        db,
        schedule_id,
        current_user,
    )

    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found.",
        )

    return schedule


@router.delete(
    "/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    removed = delete_schedule(
        db,
        schedule_id,
        current_user,
    )

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found.",
        )
