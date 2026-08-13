"""Tests for the SOC overview (KPIs, attack surface, scan health)."""

import unittest
from datetime import UTC, datetime, timedelta

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
from app.services.activity_service import record_activity
from app.services.alert_service import create_alert, create_incident
from app.services.soc_service import get_scan_health, get_soc_overview


class SocOverviewTests(unittest.TestCase):
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

        self.user = User(
            username="socadmin",
            email="soc@example.com",
            password_hash="unused",
            role=UserRole.USER,
            is_active=True,
        )
        self.db.add(self.user)
        self.db.flush()

        self.asset = Asset(
            name="Web-01",
            asset_type=AssetType.SERVER,
            ip_address="192.0.2.10",
            created_by=self.user.id,
        )
        self.db.add(self.asset)
        self.db.flush()

        self.completed = Scan(
            asset_id=self.asset.id,
            status=ScanStatus.COMPLETED,
            scanner="nmap",
        )
        self.failed = Scan(
            asset_id=self.asset.id,
            status=ScanStatus.FAILED,
            scanner="nmap",
        )
        self.db.add_all([self.completed, self.failed])
        self.db.flush()

        for scan in (self.completed, self.failed):
            result = ScanResult(
                scan_id=scan.id,
                port=443,
                protocol="tcp",
                state="open",
                service="https",
            )
            self.db.add(result)

        self.db.commit()

        self.user_id = self.user.id

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def test_scan_success_rate(self) -> None:
        overview = get_soc_overview(self.db, self.user)

        self.assertEqual(overview["scans"]["total"], 2)
        self.assertEqual(overview["scans"]["completed"], 1)
        self.assertEqual(overview["scans"]["failed"], 1)
        self.assertEqual(overview["scans"]["success_rate"], 50.0)

    def test_attack_surface_trend_contiguous(self) -> None:
        overview = get_soc_overview(self.db, self.user)

        self.assertEqual(len(overview["attack_surface_trend"]), 14)
        self.assertGreaterEqual(
            overview["attack_surface_trend"][-1]["count"],
            0,
        )

    def test_scan_health_trend(self) -> None:
        health = get_scan_health(self.db, self.user, days=7)

        self.assertEqual(len(health["trend"]), 7)
        # The estate has one completed and one failed scan today.
        total = sum(
            row["completed"] + row["failed"] for row in health["trend"]
        )
        self.assertEqual(total, 2)

    def test_alerts_incidents_counts(self) -> None:
        create_alert(
            self.db,
            user_id=self.user_id,
            alert_type="critical_vuln",
            title="Critical",
            severity="CRITICAL",
        )
        create_incident(
            self.db,
            user_id=self.user_id,
            title="Incident one",
            severity="HIGH",
        )
        self.db.commit()

        overview = get_soc_overview(self.db, self.user)

        self.assertEqual(overview["alerts"]["open"], 1)
        self.assertEqual(overview["alerts"]["critical"], 1)
        self.assertEqual(overview["incidents"]["open"], 1)
        self.assertEqual(overview["incidents"]["total"], 1)

    def test_recent_activity_included(self) -> None:
        record_activity(
            self.db,
            user_id=self.user_id,
            action="scan_completed",
            detail="Finished scan",
        )
        self.db.commit()

        overview = get_soc_overview(self.db, self.user)

        self.assertGreaterEqual(len(overview["recent_activity"]), 1)
        self.assertEqual(
            overview["recent_activity"][0]["action"],
            "scan_completed",
        )

    def test_activity_scoped_to_user(self) -> None:
        other = User(
            username="bob",
            email="bob@example.com",
            password_hash="unused",
            role=UserRole.USER,
            is_active=True,
        )
        self.db.add(other)
        self.db.commit()

        record_activity(
            self.db,
            user_id=self.user_id,
            action="login",
            detail="Signed in",
        )
        self.db.commit()

        overview = get_soc_overview(self.db, other)
        self.assertEqual(overview["recent_activity"], [])


if __name__ == "__main__":
    unittest.main()