"""Tests for the notification service and triggers."""

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.asset_types import AssetType
from app.core.roles import UserRole
from app.core.scan_status import ScanStatus
from app.database import models  # noqa: F401 - register mapped models
from app.database.base import Base
from app.models.asset import Asset
from app.models.finding import Finding
from app.models.scan import Scan
from app.models.scan_result import ScanResult
from app.models.user import User
from app.services.finding_service import update_finding_triage
from app.services.notification_service import (
    create_notification,
    list_notifications,
    mark_all_notifications_read,
    mark_notification_read,
    notify_finding_assignment,
    notify_scan_critical_findings,
    unread_notification_count,
)


class NotificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(cls.engine)
        cls.session_factory = sessionmaker(bind=cls.engine, expire_on_commit=False)

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
        self.assignee = User(
            username="assignee",
            email="assignee@example.com",
            password_hash="unused",
            role=UserRole.USER,
            is_active=True,
        )
        self.db.add_all([self.owner, self.assignee])
        self.db.flush()

        asset = Asset(
            name="Server",
            asset_type=AssetType.SERVER,
            ip_address="192.0.2.30",
            created_by=self.owner.id,
        )
        self.db.add(asset)
        self.db.flush()

        scan = Scan(
            asset_id=asset.id,
            status=ScanStatus.COMPLETED,
            scanner="nmap",
        )
        self.db.add(scan)
        self.db.flush()

        result = ScanResult(
            scan_id=scan.id,
            port=443,
            protocol="tcp",
            state="open",
            service="https",
        )
        self.db.add(result)
        self.db.flush()

        self.critical = Finding(
            scan_result_id=result.id,
            title="CVE-2024-0001",
            severity="CRITICAL",
            cve="CVE-2024-0001",
            cvss=9.8,
            status="OPEN",
        )
        self.high = Finding(
            scan_result_id=result.id,
            title="CVE-2024-0002",
            severity="HIGH",
            cve="CVE-2024-0002",
            cvss=8.1,
            status="OPEN",
        )
        self.low = Finding(
            scan_result_id=result.id,
            title="CVE-2024-0003",
            severity="LOW",
            cve="CVE-2024-0003",
            cvss=3.1,
            status="OPEN",
        )
        self.db.add_all([self.critical, self.high, self.low])
        self.db.commit()

        self.asset = asset
        self.scan = scan

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def test_critical_findings_trigger_one_aggregate_notification(self) -> None:
        notify_scan_critical_findings(
            self.db,
            self.scan,
            self.owner.id,
            [self.critical, self.high],
        )
        self.db.commit()

        result = list_notifications(self.db, self.owner.id)

        self.assertEqual(result["total"], 1)
        notification = result["items"][0]

        self.assertEqual(notification.notification_type, "critical_finding")
        self.assertEqual(notification.user_id, self.owner.id)
        self.assertEqual(notification.finding_id, self.critical.id)
        self.assertIn("1 critical and 1 high", notification.body)
        self.assertIsNone(notification.read_at)

    def test_no_notification_when_no_critical_findings(self) -> None:
        notify_scan_critical_findings(
            self.db,
            self.scan,
            self.owner.id,
            [],
        )
        self.db.commit()

        self.assertEqual(
            unread_notification_count(self.db, self.owner.id),
            0,
        )

    def test_notifications_are_scoped_to_the_user(self) -> None:
        create_notification(
            self.db,
            user_id=self.owner.id,
            notification_type="assignment",
            title="Assigned",
        )
        self.db.commit()

        owner_count = unread_notification_count(self.db, self.owner.id)
        assignee_count = unread_notification_count(self.db, self.assignee.id)

        self.assertEqual(owner_count, 1)
        self.assertEqual(assignee_count, 0)

    def test_mark_read_and_read_all(self) -> None:
        create_notification(
            self.db,
            user_id=self.owner.id,
            notification_type="assignment",
            title="One",
        )
        create_notification(
            self.db,
            user_id=self.owner.id,
            notification_type="assignment",
            title="Two",
        )
        self.db.commit()

        first = list_notifications(self.db, self.owner.id)["items"][0]

        marked = mark_notification_read(
            self.db,
            first.id,
            self.owner.id,
        )

        self.assertIsNotNone(marked.read_at)
        self.assertEqual(unread_notification_count(self.db, self.owner.id), 1)

        cleared = mark_all_notifications_read(
            self.db,
            self.owner.id,
        )

        self.assertEqual(cleared, 1)
        self.assertEqual(unread_notification_count(self.db, self.owner.id), 0)

    def test_assignment_trigger_via_triage(self) -> None:
        update_finding_triage(
            self.db,
            self.critical.id,
            self.owner,
            assignee_id=self.assignee.id,
        )

        result = list_notifications(self.db, self.assignee.id)

        self.assertEqual(result["total"], 1)
        self.assertEqual(
            result["items"][0].notification_type,
            "assignment",
        )
        self.assertEqual(
            result["items"][0].finding_id,
            self.critical.id,
        )

    def test_direct_assignment_notification(self) -> None:
        notify_finding_assignment(
            self.db,
            self.critical,
            self.assignee.id,
            self.owner,
        )
        self.db.commit()

        result = list_notifications(self.db, self.assignee.id)

        self.assertIn(
            self.critical.cve,
            result["items"][0].body,
        )


if __name__ == "__main__":
    unittest.main()
