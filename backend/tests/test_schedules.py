"""Tests for scheduled scan management and the scheduler tick."""

import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.asset_types import AssetType
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.core.roles import UserRole
from app.database import models  # noqa: F401 - register mapped models
from app.database.base import Base
from app.models.asset import Asset
from app.models.scheduled_scan import ScheduledScan
from app.models.user import User
from app.services.schedule_service import (
    compute_next_run,
    create_schedule,
    delete_schedule,
    get_due_schedules,
    list_schedules,
    run_schedule_now,
    scheduler_tick,
    update_schedule,
)
from app.schemas.schedule import (
    ScheduledScanCreate,
    ScheduledScanUpdate,
)


class ComputeNextRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base = datetime(
            2026,
            8,
            6,
            10,
            0,
            tzinfo=UTC,
        )

    def test_daily_future_time_today(self) -> None:
        result = compute_next_run(
            "DAILY",
            "14:30",
            self.base,
        )

        self.assertEqual(
            result,
            datetime(2026, 8, 6, 14, 30, tzinfo=UTC),
        )

    def test_daily_past_time_rolls_to_tomorrow(self) -> None:
        result = compute_next_run(
            "DAILY",
            "09:00",
            self.base,
        )

        self.assertEqual(
            result,
            datetime(2026, 8, 7, 9, 0, tzinfo=UTC),
        )

    def test_weekly_targets_weekday(self) -> None:
        result = compute_next_run(
            "WEEKLY",
            "08:15",
            self.base,
            week_day="MON",
        )

        # 2026-08-06 is a Thursday; next Monday is 2026-08-10.
        self.assertEqual(
            result,
            datetime(2026, 8, 10, 8, 15, tzinfo=UTC),
        )
        self.assertEqual(result.weekday(), 0)

    def test_monthly_targets_day(self) -> None:
        result = compute_next_run(
            "MONTHLY",
            "05:00",
            self.base,
            month_day=20,
        )

        self.assertEqual(
            result,
            datetime(2026, 8, 20, 5, 0, tzinfo=UTC),
        )

    def test_monthly_day_31_skips_short_months(self) -> None:
        # 2026-02-15 -> next day 31 is 2026-03-31 (February has 28 days).
        result = compute_next_run(
            "MONTHLY",
            "05:00",
            datetime(
                2026,
                2,
                15,
                10,
                0,
                tzinfo=UTC,
            ),
            month_day=31,
        )

        self.assertEqual(
            result,
            datetime(2026, 3, 31, 5, 0, tzinfo=UTC),
        )

    def test_weekly_requires_week_day(self) -> None:
        with self.assertRaises(ValidationError):
            compute_next_run(
                "WEEKLY",
                "08:00",
                self.base,
            )


class ScheduleServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(cls.engine)
        cls.session_factory = sessionmaker(
            bind=cls.engine,
            expire_on_commit=False,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def setUp(self) -> None:
        self.db: Session = self.session_factory()

        self.owner = User(
            username="owner",
            email="owner@example.com",
            password_hash="unused",
            role=UserRole.USER,
            is_active=True,
        )
        self.other = User(
            username="other",
            email="other@example.com",
            password_hash="unused",
            role=UserRole.USER,
            is_active=True,
        )
        self.admin = User(
            username="admin",
            email="admin@example.com",
            password_hash="unused",
            role=UserRole.ADMIN,
            is_active=True,
        )
        self.db.add_all([self.owner, self.other, self.admin])
        self.db.flush()

        self.asset = Asset(
            name="Web",
            asset_type=AssetType.SERVER,
            ip_address="192.0.2.40",
            created_by=self.owner.id,
        )
        self.db.add(self.asset)
        self.db.flush()
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def test_create_schedule_computes_next_run(self) -> None:
        result = create_schedule(
            self.db,
            self.owner,
            ScheduledScanCreate(
                asset_id=self.asset.id,
                cadence="DAILY",
                time_of_day="03:00",
            ),
        )

        self.assertEqual(result.asset_name, "Web")
        self.assertEqual(result.cadence, "DAILY")
        self.assertIsNotNone(result.next_run_at)
        self.assertEqual(result.next_run_at.hour, 3)
        self.assertTrue(result.enabled)

    def test_create_schedule_for_other_users_asset_rejected(self) -> None:
        with self.assertRaises(ResourceNotFoundError):
            create_schedule(
                self.db,
                self.other,
                ScheduledScanCreate(
                    asset_id=self.asset.id,
                    cadence="DAILY",
                    time_of_day="03:00",
                ),
            )

    def test_create_schedule_invalid_cadence_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            create_schedule(
                self.db,
                self.owner,
                ScheduledScanCreate(
                    asset_id=self.asset.id,
                    cadence="WEEKLY",
                    time_of_day="03:00",
                ),
            )

    def test_list_schedules_is_scoped(self) -> None:
        create_schedule(
            self.db,
            self.owner,
            ScheduledScanCreate(
                asset_id=self.asset.id,
                cadence="DAILY",
                time_of_day="03:00",
            ),
        )

        other_asset = Asset(
            name="Other",
            asset_type=AssetType.SERVER,
            ip_address="192.0.2.41",
            created_by=self.other.id,
        )
        self.db.add(other_asset)
        self.db.commit()

        create_schedule(
            self.db,
            self.other,
            ScheduledScanCreate(
                asset_id=other_asset.id,
                cadence="WEEKLY",
                time_of_day="03:00",
                week_day="MON",
            ),
        )

        self.assertEqual(len(list_schedules(self.db, self.owner)), 1)
        self.assertEqual(len(list_schedules(self.db, self.other)), 1)
        self.assertEqual(len(list_schedules(self.db, self.admin)), 2)

    def test_update_schedule_recomputes_next_run(self) -> None:
        created = create_schedule(
            self.db,
            self.owner,
            ScheduledScanCreate(
                asset_id=self.asset.id,
                cadence="DAILY",
                time_of_day="03:00",
            ),
        )

        updated = update_schedule(
            self.db,
            created.id,
            self.owner,
            ScheduledScanUpdate(
                cadence="WEEKLY",
                week_day="FRI",
            ),
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated.cadence, "WEEKLY")
        self.assertEqual(updated.week_day, "FRI")
        self.assertEqual(updated.next_run_at.weekday(), 4)

    def test_update_schedule_hidden_from_non_owner(self) -> None:
        created = create_schedule(
            self.db,
            self.owner,
            ScheduledScanCreate(
                asset_id=self.asset.id,
                cadence="DAILY",
                time_of_day="03:00",
            ),
        )

        result = update_schedule(
            self.db,
            created.id,
            self.other,
            ScheduledScanUpdate(enabled=False),
        )

        self.assertIsNone(result)

    def test_delete_schedule(self) -> None:
        created = create_schedule(
            self.db,
            self.owner,
            ScheduledScanCreate(
                asset_id=self.asset.id,
                cadence="DAILY",
                time_of_day="03:00",
            ),
        )

        removed = delete_schedule(
            self.db,
            created.id,
            self.owner,
        )

        self.assertTrue(removed)
        self.assertEqual(len(list_schedules(self.db, self.owner)), 0)

    def test_run_now_dispatches_scan_and_advances_schedule(self) -> None:
        created = create_schedule(
            self.db,
            self.owner,
            ScheduledScanCreate(
                asset_id=self.asset.id,
                cadence="DAILY",
                time_of_day="03:00",
            ),
        )

        with patch(
            "app.services.schedule_service.create_scan",
            return_value=SimpleNamespace(id=99),
        ) as mock_scan:
            result = run_schedule_now(
                self.db,
                created.id,
                self.owner,
            )

        mock_scan.assert_called_once()
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.last_run_at)
        self.assertIsNotNone(result.next_run_at)
        self.assertGreater(result.next_run_at, result.last_run_at)

    def test_scheduler_tick_dispatches_due_schedules(self) -> None:
        created = create_schedule(
            self.db,
            self.owner,
            ScheduledScanCreate(
                asset_id=self.asset.id,
                cadence="DAILY",
                time_of_day="03:00",
            ),
        )

        now = datetime.now(UTC)
        schedule = (
            self.db.query(ScheduledScan)
            .filter(
                ScheduledScan.id == created.id,
            )
            .first()
        )
        schedule.next_run_at = now - timedelta(hours=1)
        self.db.commit()

        with patch(
            "app.services.schedule_service.create_scan",
            return_value=SimpleNamespace(id=99),
        ) as mock_scan:
            dispatched = scheduler_tick(self.db, now)

        self.assertEqual(dispatched, 1)
        mock_scan.assert_called_once()

        schedule = (
            self.db.query(ScheduledScan)
            .filter(
                ScheduledScan.id == created.id,
            )
            .first()
        )
        self.assertGreater(schedule.next_run_at, now)

    def test_scheduler_skips_disabled_schedules(self) -> None:
        created = create_schedule(
            self.db,
            self.owner,
            ScheduledScanCreate(
                asset_id=self.asset.id,
                cadence="DAILY",
                time_of_day="03:00",
            ),
        )

        now = datetime.now(UTC)
        schedule = (
            self.db.query(ScheduledScan)
            .filter(
                ScheduledScan.id == created.id,
            )
            .first()
        )
        schedule.next_run_at = now - timedelta(hours=1)
        schedule.enabled = False
        self.db.commit()

        with patch(
            "app.services.schedule_service.create_scan",
        ) as mock_scan:
            dispatched = scheduler_tick(self.db, now)

        self.assertEqual(dispatched, 0)
        mock_scan.assert_not_called()
        self.assertEqual(len(get_due_schedules(self.db, now)), 0)


if __name__ == "__main__":
    unittest.main()
