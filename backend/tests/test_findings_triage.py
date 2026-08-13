"""Tests for the findings triage center service."""

import unittest
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.asset_types import AssetType
from app.core.exceptions import ResourceNotFoundError
from app.core.roles import UserRole
from app.core.scan_status import ScanStatus
from app.database import models  # noqa: F401 - register mapped models
from app.database.base import Base
from app.models.asset import Asset
from app.models.finding import Finding
from app.models.scan import Scan
from app.models.scan_result import ScanResult
from app.models.user import User
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


def _make_scan(
    db: Session,
    asset: Asset,
) -> Scan:
    scan = Scan(
        asset_id=asset.id,
        status=ScanStatus.COMPLETED,
        scanner="nmap",
    )
    db.add(scan)
    db.flush()
    return scan


def _make_result(
    db: Session,
    scan: Scan,
) -> ScanResult:
    result = ScanResult(
        scan_id=scan.id,
        port=443,
        protocol="tcp",
        state="open",
        service="https",
        cpe="cpe:/a:apache:http_server",
    )
    db.add(result)
    db.flush()
    return result


def _make_finding(
    db: Session,
    result: ScanResult,
    *,
    severity: str = "HIGH",
    status: str = "OPEN",
    cve: str | None = "CVE-2024-0001",
) -> Finding:
    finding = Finding(
        scan_result_id=result.id,
        title=cve or "Test finding",
        severity=severity,
        cve=cve,
        cvss=7.5,
        status=status,
        description="Description",
        recommendation="Remediate.",
    )
    db.add(finding)
    db.flush()
    return finding


class FindingsTriageTests(unittest.TestCase):
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
            ip_address="192.0.2.20",
            created_by=self.alice.id,
        )
        bob_asset = Asset(
            name="Bob Asset",
            asset_type=AssetType.SERVER,
            ip_address="192.0.2.21",
            created_by=self.bob.id,
        )
        self.db.add_all([alice_asset, bob_asset])
        self.db.flush()

        alice_scan = _make_scan(self.db, alice_asset)
        bob_scan = _make_scan(self.db, bob_asset)

        self.alice_result = _make_result(self.db, alice_scan)
        self.bob_result = _make_result(self.db, bob_scan)

        self.alice_finding = _make_finding(
            self.db,
            self.alice_result,
            severity="CRITICAL",
        )
        self.alice_low = _make_finding(
            self.db,
            self.alice_result,
            severity="LOW",
            status="RESOLVED",
            cve="CVE-2024-0002",
        )
        self.bob_finding = _make_finding(
            self.db,
            self.bob_result,
            severity="MEDIUM",
            cve="CVE-2024-0003",
        )
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    # -- triage updates -------------------------------------------------

    def test_triage_status_change_records_activity(self) -> None:
        updated = update_finding_triage(
            self.db,
            self.alice_finding.id,
            self.alice,
            status="IN_PROGRESS",
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated["status"], "IN_PROGRESS")

        activities = get_finding_activities(
            self.db,
            self.alice_finding.id,
            self.alice,
        )

        self.assertIsNotNone(activities)
        self.assertEqual(activities[0]["action"], "status")
        self.assertEqual(activities[0]["old_value"], "OPEN")
        self.assertEqual(activities[0]["new_value"], "IN_PROGRESS")
        self.assertEqual(activities[0]["username"], "alice")

    def test_triage_assignee_records_activity(self) -> None:
        updated = update_finding_triage(
            self.db,
            self.alice_finding.id,
            self.alice,
            assignee_id=self.bob.id,
        )

        self.assertEqual(updated["assigned_to"], self.bob.id)
        self.assertEqual(updated["assigned_to_name"], "bob")

        activities = get_finding_activities(
            self.db,
            self.alice_finding.id,
            self.alice,
        )

        self.assertEqual(activities[0]["action"], "assignee")
        self.assertEqual(activities[0]["new_value"], f"user:{self.bob.id}")

    def test_triage_unassigns_when_explicit_null(self) -> None:
        update_finding_triage(
            self.db,
            self.alice_finding.id,
            self.alice,
            assignee_id=self.bob.id,
        )
        updated = update_finding_triage(
            self.db,
            self.alice_finding.id,
            self.alice,
            assignee_id=None,
        )

        self.assertIsNone(updated["assigned_to"])
        self.assertIsNone(updated["assigned_to_name"])

    def test_triage_invalid_assignee_raises(self) -> None:
        with self.assertRaises(ResourceNotFoundError):
            update_finding_triage(
                self.db,
                self.alice_finding.id,
                self.alice,
                assignee_id=9999,
            )

    def test_triage_notes_and_due_date(self) -> None:
        due = datetime.now(UTC) + timedelta(days=7)

        updated = update_finding_triage(
            self.db,
            self.alice_finding.id,
            self.alice,
            notes="Verified against staging.",
            due_date=due,
        )

        self.assertEqual(updated["notes"], "Verified against staging.")
        self.assertIsNotNone(updated["due_date"])

    def test_legacy_status_endpoint_path(self) -> None:
        updated = update_finding_status(
            self.db,
            self.alice_finding.id,
            "ACCEPTED_RISK",
            self.alice,
        )
        self.assertEqual(updated["status"], "ACCEPTED_RISK")

    def test_out_of_scope_finding_returns_none(self) -> None:
        result = update_finding_triage(
            self.db,
            self.bob_finding.id,
            self.alice,
            status="RESOLVED",
        )
        self.assertIsNone(result)

    # -- bulk -----------------------------------------------------------

    def test_bulk_status_update_scopes_to_user(self) -> None:
        result = bulk_update_findings_status(
            self.db,
            [self.alice_finding.id, self.bob_finding.id],
            "IN_PROGRESS",
            self.alice,
        )

        self.assertEqual(result["updated"], 1)
        self.assertEqual(result["ids"], [self.alice_finding.id])

        fresh = get_finding(self.db, self.bob_finding.id, self.alice)
        self.assertIsNone(fresh)

        fresh_bob = get_finding(self.db, self.bob_finding.id, self.bob)
        self.assertEqual(fresh_bob["status"], "OPEN")

    def test_bulk_status_skips_unchanged(self) -> None:
        result = bulk_update_findings_status(
            self.db,
            [self.alice_low.id],
            "RESOLVED",
            self.alice,
        )
        self.assertEqual(result["updated"], 0)

    # -- stats / export / list -----------------------------------------

    def test_findings_stats_rollup(self) -> None:
        stats = get_findings_stats(self.db, self.alice)

        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["open"], 1)
        self.assertEqual(stats["resolved"], 1)
        self.assertEqual(stats["by_severity"]["CRITICAL"], 1)
        self.assertEqual(stats["by_severity"]["LOW"], 1)

        admin_stats = get_findings_stats(self.db, self.admin)
        self.assertEqual(admin_stats["total"], 3)

    def test_export_csv_contains_header_and_scoped_rows(self) -> None:
        csv_content = export_findings_csv(self.db, self.alice)

        self.assertIn("id,cve,title,severity,cvss,status", csv_content)
        self.assertIn("CVE-2024-0001", csv_content)
        self.assertNotIn("CVE-2024-0003", csv_content)

    def test_list_includes_assignee_and_due_date(self) -> None:
        due = datetime.now(UTC) + timedelta(days=3)
        update_finding_triage(
            self.db,
            self.alice_finding.id,
            self.alice,
            assignee_id=self.bob.id,
            due_date=due,
        )

        listing = get_findings(self.db, self.alice)

        item = next(
            row
            for row in listing["items"]
            if row["id"] == self.alice_finding.id
        )
        self.assertEqual(item["assigned_to"], self.bob.id)
        self.assertEqual(item["assigned_to_name"], "bob")
        self.assertIsNotNone(item["due_date"])

    def test_assigned_me_filter(self) -> None:
        update_finding_triage(
            self.db,
            self.alice_finding.id,
            self.alice,
            assignee_id=self.alice.id,
        )

        mine = get_findings(
            self.db,
            self.alice,
            assigned="me",
        )
        self.assertEqual(mine["total"], 1)

        unassigned = get_findings(
            self.db,
            self.alice,
            assigned="unassigned",
        )
        self.assertEqual(unassigned["total"], 1)
        self.assertEqual(
            unassigned["items"][0]["id"],
            self.alice_low.id,
        )

    def test_assignees_returns_active_users_only(self) -> None:
        assignees = list_findings_assignees(self.db)

        usernames = {item["username"] for item in assignees}

        self.assertEqual(
            usernames,
            {"admin", "alice", "bob"},
        )


if __name__ == "__main__":
    unittest.main()
