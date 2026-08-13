"""Tests for scan serialization, including scan profile round-tripping."""

import unittest
from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.asset_types import AssetType
from app.core.roles import UserRole
from app.core.scan_profile import ScanProfile
from app.core.scan_status import ScanStatus
from app.database import models  # noqa: F401 - register mapped models
from app.database.base import Base
from app.models.asset import Asset
from app.models.scan import Scan
from app.models.user import User
from app.services.scan_service import get_scan, get_scans


class ScanSerializationTests(unittest.TestCase):
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
        self.alice = User(
            username="alice",
            email="alice@example.com",
            password_hash="unused",
            role=UserRole.USER,
            is_active=True,
        )
        self.db.add(self.alice)
        self.db.flush()

        self.asset = Asset(
            name="Alice Asset",
            asset_type=AssetType.SERVER,
            ip_address="192.0.2.10",
            created_by=self.alice.id,
        )
        self.db.add(self.asset)
        self.db.flush()

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def _make_scan(self, profile: str) -> Scan:
        scan = Scan(
            asset_id=self.asset.id,
            status=ScanStatus.RUNNING,
            scanner="nmap",
            scan_profile=profile,
            started_at=datetime.now(UTC),
        )
        self.db.add(scan)
        self.db.commit()
        self.db.refresh(scan)
        return scan

    def test_get_scans_returns_stored_scan_profile(self) -> None:
        self._make_scan(ScanProfile.FULL.value)

        scans = get_scans(self.db, self.alice)

        self.assertEqual(len(scans), 1)
        self.assertEqual(scans[0].scan_profile, ScanProfile.FULL)
        self.assertNotEqual(scans[0].scan_profile, ScanProfile.STANDARD)

    def test_get_scans_defaults_standard_profile(self) -> None:
        self._make_scan(ScanProfile.STANDARD.value)

        scans = get_scans(self.db, self.alice)

        self.assertEqual(len(scans), 1)
        self.assertEqual(scans[0].scan_profile, ScanProfile.STANDARD)

    def test_get_scan_returns_stored_scan_profile(self) -> None:
        scan = self._make_scan(ScanProfile.FULL.value)

        result = get_scan(self.db, scan.id, self.alice)

        self.assertIsNotNone(result)
        self.assertEqual(result.scan_profile, ScanProfile.FULL)

    def test_scan_profile_is_not_always_standard(self) -> None:
        self._make_scan(ScanProfile.FULL.value)
        self._make_scan(ScanProfile.STANDARD.value)

        scans = get_scans(self.db, self.alice)

        profiles = {s.scan_profile for s in scans}
        self.assertIn(ScanProfile.FULL, profiles)
        self.assertIn(ScanProfile.STANDARD, profiles)


if __name__ == "__main__":
    unittest.main()
