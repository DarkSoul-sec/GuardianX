from datetime import UTC, datetime, time as dt_time, timedelta

from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.core.roles import UserRole
from app.services.query_helpers import apply_asset_scope
from app.logger import logger
from app.models.asset import Asset
from app.models.scheduled_scan import ScheduledScan
from app.models.user import User
from app.schemas.schedule import (
    ScheduledScanCreate,
    ScheduledScanResponse,
    ScheduledScanUpdate,
)
from app.services.scan_service import create_scan

_WEEK_ORDER = {
    "MON": 0,
    "TUE": 1,
    "WED": 2,
    "THU": 3,
    "FRI": 4,
    "SAT": 5,
    "SUN": 6,
}


def _parse_time(value: str) -> dt_time:
    hour, minute = value.split(":")
    return dt_time(int(hour), int(minute))


def compute_next_run(
    cadence: str,
    time_of_day: str,
    now: datetime,
    week_day: str | None = None,
    month_day: int | None = None,
) -> datetime:
    """
    Compute the next UTC run for a schedule strictly after ``now``.
    """

    if cadence == "WEEKLY" and week_day not in _WEEK_ORDER:
        raise ValidationError("week_day is required for weekly cadence.")

    if cadence == "MONTHLY" and not month_day:
        raise ValidationError("month_day is required for monthly cadence.")

    target = _parse_time(time_of_day)
    candidate = datetime.combine(
        now.date(),
        target,
        tzinfo=now.tzinfo,
    )

    if candidate <= now:
        candidate += timedelta(days=1)

    if cadence == "DAILY":
        return candidate

    if cadence == "WEEKLY":
        target_weekday = _WEEK_ORDER[week_day]

        while candidate.weekday() != target_weekday:
            candidate += timedelta(days=1)

        return candidate

    if cadence == "MONTHLY":
        # Worst case ~59 days to reach the target day in the next month.
        for _ in range(62):
            if candidate.day == month_day and candidate > now:
                return candidate

            candidate += timedelta(days=1)

        raise ValidationError("Could not compute the next monthly run.")

    raise ValidationError(f"Unknown cadence: {cadence}")


def _validate_schedule(
    cadence: str,
    time_of_day: str,
    week_day: str | None,
    month_day: int | None,
) -> None:
    _parse_time(time_of_day)

    if cadence not in ("DAILY", "WEEKLY", "MONTHLY"):
        raise ValidationError(f"Unknown cadence: {cadence}")

    if cadence == "WEEKLY" and week_day not in _WEEK_ORDER:
        raise ValidationError("week_day is required for weekly cadence.")

    if cadence == "MONTHLY" and not month_day:
        raise ValidationError("month_day is required for monthly cadence.")


def _serialize(
    schedule: ScheduledScan,
    asset_name: str | None,
) -> ScheduledScanResponse:
    return ScheduledScanResponse(
        id=schedule.id,
        asset_id=schedule.asset_id,
        asset_name=asset_name,
        scanner=schedule.scanner,
        cadence=schedule.cadence,
        time_of_day=schedule.time_of_day,
        week_day=schedule.week_day,
        month_day=schedule.month_day,
        enabled=schedule.enabled,
        last_run_at=schedule.last_run_at,
        next_run_at=schedule.next_run_at,
        created_by=schedule.created_by,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )


def list_schedules(
    db: Session,
    current_user: User,
) -> list[ScheduledScanResponse]:
    query = (
        db.query(
            ScheduledScan,
            Asset.name.label("asset_name"),
        )
        .join(
            Asset,
            ScheduledScan.asset_id == Asset.id,
        )
    )

    query = apply_asset_scope(query, current_user)

    rows = query.order_by(
        ScheduledScan.created_at.desc(),
    ).all()

    return [
        _serialize(schedule, asset_name)
        for schedule, asset_name in rows
    ]


def get_schedule(
    db: Session,
    schedule_id: int,
    current_user: User,
) -> ScheduledScan | None:
    query = (
        db.query(ScheduledScan)
        .join(
            Asset,
            ScheduledScan.asset_id == Asset.id,
        )
        .filter(
            ScheduledScan.id == schedule_id,
        )
    )

    query = apply_asset_scope(query, current_user)

    return query.first()


def create_schedule(
    db: Session,
    current_user: User,
    data: ScheduledScanCreate,
) -> ScheduledScanResponse:
    _validate_schedule(
        data.cadence,
        data.time_of_day,
        data.week_day,
        data.month_day,
    )

    asset = (
        db.query(Asset)
        .filter(
            Asset.id == data.asset_id,
        )
        .first()
    )

    if asset is None:
        raise ResourceNotFoundError("Asset not found.")

    if (
        current_user.role != UserRole.ADMIN
        and asset.created_by != current_user.id
    ):
        raise ResourceNotFoundError("Asset not found.")

    now = datetime.now(UTC)

    schedule = ScheduledScan(
        asset_id=data.asset_id,
        scanner=data.scanner,
        cadence=data.cadence,
        time_of_day=data.time_of_day,
        week_day=data.week_day,
        month_day=data.month_day,
        enabled=data.enabled,
        created_by=current_user.id,
        next_run_at=compute_next_run(
            data.cadence,
            data.time_of_day,
            now,
            data.week_day,
            data.month_day,
        ),
    )

    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    return _serialize(
        schedule,
        asset.name,
    )


def update_schedule(
    db: Session,
    schedule_id: int,
    current_user: User,
    data: ScheduledScanUpdate,
) -> ScheduledScanResponse | None:
    schedule = get_schedule(
        db,
        schedule_id,
        current_user,
    )

    if schedule is None:
        return None

    cadence = data.cadence or schedule.cadence
    time_of_day = data.time_of_day or schedule.time_of_day

    if data.week_day is not None:
        week_day = data.week_day
    else:
        week_day = schedule.week_day

    if data.month_day is not None:
        month_day = data.month_day
    else:
        month_day = schedule.month_day

    _validate_schedule(
        cadence,
        time_of_day,
        week_day,
        month_day,
    )

    schedule.cadence = cadence
    schedule.time_of_day = time_of_day
    schedule.week_day = week_day
    schedule.month_day = month_day

    if data.scanner is not None:
        schedule.scanner = data.scanner

    if data.enabled is not None:
        schedule.enabled = data.enabled

    if schedule.enabled:
        schedule.next_run_at = compute_next_run(
            cadence,
            time_of_day,
            datetime.now(UTC),
            week_day,
            month_day,
        )

    db.commit()
    db.refresh(schedule)

    asset = (
        db.query(Asset.name)
        .filter(
            Asset.id == schedule.asset_id,
        )
        .scalar()
    )

    return _serialize(
        schedule,
        asset,
    )


def delete_schedule(
    db: Session,
    schedule_id: int,
    current_user: User,
) -> bool:
    schedule = get_schedule(
        db,
        schedule_id,
        current_user,
    )

    if schedule is None:
        return False

    db.delete(schedule)
    db.commit()

    return True


def run_schedule_now(
    db: Session,
    schedule_id: int,
    current_user: User,
) -> ScheduledScanResponse | None:
    schedule = get_schedule(
        db,
        schedule_id,
        current_user,
    )

    if schedule is None:
        return None

    asset = (
        db.query(Asset)
        .filter(
            Asset.id == schedule.asset_id,
        )
        .first()
    )

    if asset is None:
        raise ResourceNotFoundError("Asset not found.")

    create_scan(
        db,
        asset,
    )

    now = datetime.now(UTC)

    schedule.last_run_at = now
    schedule.next_run_at = compute_next_run(
        schedule.cadence,
        schedule.time_of_day,
        now,
        schedule.week_day,
        schedule.month_day,
    )

    db.commit()
    db.refresh(schedule)

    return _serialize(
        schedule,
        asset.name,
    )


def get_due_schedules(
    db: Session,
    now: datetime,
) -> list[ScheduledScan]:
    return (
        db.query(ScheduledScan)
        .filter(
            ScheduledScan.enabled.is_(True),
        )
        .filter(
            ScheduledScan.next_run_at.isnot(None),
        )
        .filter(
            ScheduledScan.next_run_at <= now,
        )
        .with_for_update(
            skip_locked=True,
        )
        .all()
    )


def scheduler_tick(
    db: Session,
    now: datetime | None = None,
) -> int:
    """
    Dispatch every due schedule and advance its next run.
    """

    now = now or datetime.now(UTC)
    due = get_due_schedules(
        db,
        now,
    )

    dispatched = 0

    for schedule in due:
        try:
            asset = (
                db.query(Asset)
                .filter(
                    Asset.id == schedule.asset_id,
                )
                .first()
            )

            if asset is None:
                logger.warning(
                    "Skipping schedule %s: asset %s no longer exists.",
                    schedule.id,
                    schedule.asset_id,
                )
                schedule.enabled = False
                continue

            schedule.last_run_at = now
            schedule.next_run_at = compute_next_run(
                schedule.cadence,
                schedule.time_of_day,
                now,
                schedule.week_day,
                schedule.month_day,
            )

            create_scan(
                db,
                asset,
            )

            dispatched += 1
        except Exception:
            logger.exception(
                "Skipping schedule %s: dispatch failed.",
                schedule.id,
            )
            db.rollback()
            continue

    db.commit()

    if dispatched:
        logger.info(
            "Scheduler dispatched %d scheduled scan(s).",
            dispatched,
        )

    return dispatched
