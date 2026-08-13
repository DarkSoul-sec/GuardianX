"""Tests for the scan operations endpoint service and executor status."""

import unittest
from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.asset_types import AssetType
from app.core.roles import UserRole
from app.core.scan_status import ScanStatus
from app.database import models  # noqa: F401 - register mapped models
from app.database.base import Base
from app.models.asset import Asset
from app.models.scan import Scan
from app.models.user import User
from app.services.scan_service import get_scan_operations
from app.tasks.scan_worker import scan_executor


class ScanOperationsTests(unittest.TestCase):
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
        self.admin = User(
            username="admin",
            email="admin@example.com",
            password_hash="unused",
            role=UserRole.ADMIN,
            is_active=True,
        )
        self.alice = User(
            username="alice",
            email="alice@example.com",
            password_hash="unused",
            role=UserRole.USER,
            is_active=True,
        )
        self.bob = User(
            username="bob",
            email="bob@example.com",
            password_hash="unused",
            role=UserRole.USER,
            is_active=True,
        )
        self.db.add_all([self.admin, self.alice, self.bob])
        self.db.flush()

        alice_asset = Asset(
            name="Alice Asset",
            asset_type=AssetType.SERVER,
            ip_address="192.0.2.10",
            created_by=self.alice.id,
        )
        bob_asset = Asset(
            name="Bob Asset",
            asset_type=AssetType.SERVER,
            ip_address="192.0.2.11",
            created_by=self.bob.id,
        )
        self.db.add_all([alice_asset, bob_asset])
        self.db.flush()

        self.db.add_all(
            [
                Scan(
                    asset_id=alice_asset.id,
                    status=ScanStatus.COMPLETED,
                    scanner="nmap",
                    started_at=datetime.now(UTC),
                    finished_at=datetime.now(UTC),
                ),
                Scan(
                    asset_id=alice_asset.id,
                    status=ScanStatus.RUNNING,
                    scanner="nmap",
                    started_at=datetime.now(UTC),
                ),
                Scan(
                    asset_id=bob_asset.id,
                    status=ScanStatus.FAILED,
                    scanner="nmap",
                    started_at=datetime.now(UTC),
                    finished_at=datetime.now(UTC),
                ),
            ]
        )
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def test_executor_status_reports_a_valid_snapshot(self) -> None:
        status_snapshot = scan_executor.status()

        self.assertIn("max_workers", status_snapshot)
        self.assertIn("queued", status_snapshot)
        self.assertIn("running", status_snapshot)
        self.assertIn("idle_workers", status_snapshot)
        self.assertIn("closed", status_snapshot)

        self.assertGreaterEqual(status_snapshot["max_workers"], 1)
        self.assertGreaterEqual(status_snapshot["queued"], 0)
        self.assertGreaterEqual(status_snapshot["running"], 0)
        self.assertGreaterEqual(status_snapshot["idle_workers"], 0)
        self.assertEqual(
            status_snapshot["idle_workers"],
            max(0, status_snapshot["max_workers"] - status_snapshot["running"]),
        )
        self.assertFalse(status_snapshot["closed"])

    def test_operations_counts_are_scoped_to_the_user(self) -> None:
        alice_ops = get_scan_operations(self.db, self.alice)

        self.assertEqual(alice_ops.total, 2)
        self.assertEqual(alice_ops.counts["COMPLETED"], 1)
        self.assertEqual(alice_ops.counts["RUNNING"], 1)
        self.assertNotIn("FAILED", alice_ops.counts)

        admin_ops = get_scan_operations(self.db, self.admin)

        self.assertEqual(admin_ops.total, 3)
        self.assertEqual(admin_ops.counts["FAILED"], 1)
        self.assertEqual(admin_ops.executor.max_workers, scan_executor.max_workers)

    def test_operations_includes_executor_state(self) -> None:
        ops = get_scan_operations(self.db, self.admin)

        self.assertEqual(ops.executor.max_workers, scan_executor.max_workers)
        self.assertEqual(ops.executor.queued, scan_executor.queued)
        self.assertEqual(ops.executor.running, scan_executor.running)
        self.assertEqual(ops.executor.closed, scan_executor.closed)


if __name__ == "__main__":
    unittest.main()
