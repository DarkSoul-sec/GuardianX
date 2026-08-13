"""Integration tests for resource visibility and administrator access."""

import unittest
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.asset_types import AssetType
from app.core.roles import UserRole
from app.core.scan_status import ScanStatus
from app.database import models  # noqa: F401 - register mapped models
from app.database.base import Base
from app.api.v1.assets import edit_asset, get_asset, list_assets
from app.api.v1.dashboard import dashboard, dashboard_overview
from app.api.v1.findings import change_status, list_findings, retrieve_finding
from app.api.v1.scans import list_scans, retrieve_scan, retrieve_scan_results
from app.models.asset import Asset
from app.models.finding import Finding
from app.models.scan import Scan
from app.models.scan_result import ScanResult
from app.models.user import User
from app.schemas.finding import FindingStatus, FindingStatusUpdate
from app.services.scan_service import get_asset_for_scan


class OwnershipIsolationTests(unittest.TestCase):
    """Exercise ownership rules through the published API endpoints."""

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

        self.alice_asset = Asset(
            name="Alice Asset",
            asset_type=AssetType.SERVER,
            ip_address="192.0.2.10",
            created_by=self.alice.id,
        )
        self.bob_asset = Asset(
            name="Bob Asset",
            asset_type=AssetType.SERVER,
            ip_address="192.0.2.11",
            created_by=self.bob.id,
        )
        self.db.add_all([self.alice_asset, self.bob_asset])
        self.db.flush()

        self.alice_scan = Scan(
            asset_id=self.alice_asset.id,
            status=ScanStatus.COMPLETED,
            scanner="nmap",
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
        )
        self.bob_scan = Scan(
            asset_id=self.bob_asset.id,
            status=ScanStatus.COMPLETED,
            scanner="nmap",
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
        )
        self.db.add_all([self.alice_scan, self.bob_scan])
        self.db.flush()

        alice_result = ScanResult(
            scan_id=self.alice_scan.id,
            port=443,
            protocol="tcp",
            state="open",
            service="https",
            is_ssl=True,
        )
        bob_result = ScanResult(
            scan_id=self.bob_scan.id,
            port=22,
            protocol="tcp",
            state="open",
            service="ssh",
            is_ssl=False,
        )
        self.db.add_all([alice_result, bob_result])
        self.db.flush()

        self.alice_finding = Finding(
            scan_result_id=alice_result.id,
            title="Alice finding",
            severity="HIGH",
            status="OPEN",
        )
        self.bob_finding = Finding(
            scan_result_id=bob_result.id,
            title="Bob finding",
            severity="CRITICAL",
            status="OPEN",
        )
        self.db.add_all([self.alice_finding, self.bob_finding])
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def test_standard_user_isolated_from_other_users_assets_and_scans(self) -> None:
        assets = list_assets(db=self.db, current_user=self.alice)
        self.assertEqual([asset.id for asset in assets], [self.alice_asset.id])
        with self.assertRaises(HTTPException) as error:
            get_asset(self.bob_asset.id, db=self.db, current_user=self.alice)
        self.assertEqual(error.exception.status_code, 404)
        with self.assertRaises(HTTPException) as error:
            edit_asset(self.bob_asset.id, data={}, db=self.db, current_user=self.alice)
        self.assertEqual(error.exception.status_code, 404)

        scans = list_scans(db=self.db, current_user=self.alice)
        self.assertEqual([scan.id for scan in scans], [self.alice_scan.id])
        with self.assertRaises(HTTPException) as error:
            retrieve_scan(self.bob_scan.id, db=self.db, current_user=self.alice)
        self.assertEqual(error.exception.status_code, 404)
        with self.assertRaises(HTTPException) as error:
            retrieve_scan_results(self.bob_scan.id, db=self.db, current_user=self.alice)
        self.assertEqual(error.exception.status_code, 404)
        self.assertIsNone(get_asset_for_scan(self.db, self.bob_asset.id, self.alice))

    def test_standard_user_isolated_from_findings_and_dashboard(self) -> None:
        findings = list_findings(
            db=self.db,
            current_user=self.alice,
            severity=None,
            status=None,
            asset=None,
            scan=None,
            cve=None,
            search=None,
            page=1,
            size=20,
            sort_by="created_at",
            sort_order="desc",
        )
        self.assertEqual(findings["total"], 1)
        self.assertEqual(findings["items"][0]["id"], self.alice_finding.id)
        with self.assertRaises(HTTPException) as error:
            retrieve_finding(self.bob_finding.id, db=self.db, current_user=self.alice)
        self.assertEqual(error.exception.status_code, 404)
        with self.assertRaises(HTTPException) as error:
            change_status(
                self.bob_finding.id,
                payload=FindingStatusUpdate(status=FindingStatus.RESOLVED),
                db=self.db,
                current_user=self.alice,
            )
        self.assertEqual(error.exception.status_code, 404)

        dashboard_response = dashboard(db=self.db, current_user=self.alice)
        self.assertEqual(dashboard_response["total_assets"], 1)
        self.assertEqual(dashboard_response["total_scans"], 1)
        self.assertEqual(dashboard_response["open_ports"], 1)

        overview = dashboard_overview(db=self.db, current_user=self.alice)
        self.assertEqual(overview["assets"], 1)
        self.assertEqual(overview["total_findings"], 1)

        self.assertEqual(
            overview["asset_distribution"],
            [{"type": "SERVER", "count": 1}],
        )
        self.assertEqual(len(overview["findings_trend"]), 14)
        self.assertEqual(overview["findings_trend"][-1]["high"], 1)
        self.assertEqual(overview["findings_trend"][-1]["critical"], 0)
        self.assertEqual(
            overview["top_vulnerabilities"],
            [
                {
                    "cve": None,
                    "title": "Alice finding",
                    "severity": "HIGH",
                    "cvss": None,
                    "status": "OPEN",
                    "asset": "Alice Asset",
                }
            ],
        )

    def test_administrator_can_access_all_resources(self) -> None:
        self.assertEqual(len(list_assets(db=self.db, current_user=self.admin)), 2)
        self.assertIsNotNone(get_asset(self.bob_asset.id, db=self.db, current_user=self.admin))
        self.assertEqual(len(list_scans(db=self.db, current_user=self.admin)), 2)
        self.assertIsNotNone(retrieve_scan(self.bob_scan.id, db=self.db, current_user=self.admin))
        self.assertEqual(
            list_findings(
                db=self.db,
                current_user=self.admin,
                severity=None,
                status=None,
                asset=None,
                scan=None,
                cve=None,
                search=None,
                page=1,
                size=20,
                sort_by="created_at",
                sort_order="desc",
            )["total"],
            2,
        )
        self.assertIsNotNone(retrieve_finding(self.bob_finding.id, db=self.db, current_user=self.admin))
        self.assertIsNotNone(get_asset_for_scan(self.db, self.bob_asset.id, self.admin))

        dashboard_response = dashboard(db=self.db, current_user=self.admin)
        self.assertEqual(dashboard_response["total_assets"], 2)
        self.assertEqual(dashboard_response["total_scans"], 2)


if __name__ == "__main__":
    unittest.main()
