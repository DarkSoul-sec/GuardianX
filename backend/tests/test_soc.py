"""Tests for the SOC alert and incident services."""

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.asset_types import AssetType
from app.core.roles import UserRole
from app.core.scan_status import ScanStatus
from app.database import models  # noqa: F401 - register mapped models
from app.database.base import Base
from app.models.alert import Alert
from app.models.asset import Asset
from app.models.finding import Finding
from app.models.incident import Incident
from app.models.scan import Scan
from app.models.scan_result import ScanResult
from app.models.user import User
from app.services.alert_service import (
    create_alert,
    create_incident,
    evaluate_finding_alert,
    get_incident,
    list_alerts,
    list_incidents,
    notify_scan_outcome_alert,
    update_alert_status,
    update_incident,
)


class AlertIncidentTests(unittest.TestCase):
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
            username="socowner",
            email="owner@example.com",
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

        self.scan = Scan(
            asset_id=self.asset.id,
            status=ScanStatus.COMPLETED,
            scanner="nmap",
        )
        self.db.add(self.scan)
        self.db.flush()

        self.result = ScanResult(
            scan_id=self.scan.id,
            port=443,
            protocol="tcp",
            state="open",
            service="https",
        )
        self.db.add(self.result)
        self.db.flush()

        self.finding = Finding(
            scan_result_id=self.result.id,
            title="CVE-2024-9999",
            severity="CRITICAL",
            cve="CVE-2024-9999",
            cvss=9.8,
            status="OPEN",
        )
        self.db.add(self.finding)
        self.db.commit()

        self.user_id = self.user.id

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def test_create_alert_and_list(self) -> None:
        create_alert(
            self.db,
            user_id=self.user_id,
            alert_type="critical_vuln",
            title="Critical vulnerability",
            severity="CRITICAL",
            finding_id=self.finding.id,
        )
        self.db.commit()

        result = list_alerts(self.db, self.user_id)

        self.assertEqual(result["total"], 1)
        self.assertEqual(result["open"], 1)
        alert = result["items"][0]
        self.assertEqual(alert.alert_type, "critical_vuln")
        self.assertEqual(alert.status, "OPEN")

    def test_alert_scoped_to_user(self) -> None:
        other = User(
            username="other",
            email="other@example.com",
            password_hash="unused",
            role=UserRole.USER,
            is_active=True,
        )
        self.db.add(other)
        self.db.commit()

        create_alert(
            self.db,
            user_id=self.user_id,
            alert_type="scan_failed",
            title="failed",
            severity="HIGH",
        )
        self.db.commit()

        self.assertEqual(list_alerts(self.db, other.id)["total"], 0)
        self.assertEqual(list_alerts(self.db, self.user_id)["total"], 1)

    def test_acknowledge_and_resolve(self) -> None:
        alert = create_alert(
            self.db,
            user_id=self.user_id,
            alert_type="kev",
            title="KEV",
            severity="HIGH",
        )
        self.db.commit()

        update_alert_status(self.db, alert, "ACKNOWLEDGED")
        update_alert_status(self.db, alert, "RESOLVED")

        self.assertEqual(alert.status, "RESOLVED")
        self.assertIsNotNone(alert.resolved_at)

    def test_evaluate_finding_alert_only_critical(self) -> None:
        alert = evaluate_finding_alert(
            self.db,
            self.finding,
            user_id=self.user_id,
        )
        self.db.commit()

        self.assertIsNotNone(alert)
        self.assertEqual(alert.alert_type, "critical_vuln")
        self.assertEqual(alert.asset_id, self.asset.id)

    def test_scan_failed_alert(self) -> None:
        alert = notify_scan_outcome_alert(
            self.db,
            self.scan,
            self.asset,
            success=False,
        )
        self.db.commit()

        self.assertIsNotNone(alert)
        self.assertEqual(alert.alert_type, "scan_failed")
        self.assertIn("Web-01", alert.title)

    def test_no_scan_success_alert(self) -> None:
        self.assertIsNone(
            notify_scan_outcome_alert(
                self.db,
                self.scan,
                self.asset,
                success=True,
            )
        )

    def test_create_and_update_incident(self) -> None:
        alert = create_alert(
            self.db,
            user_id=self.user_id,
            alert_type="critical_vuln",
            title="Critical",
            severity="CRITICAL",
            finding_id=self.finding.id,
        )
        self.db.commit()

        incident = create_incident(
            self.db,
            user_id=self.user_id,
            title="Ransomware attempt",
            severity="CRITICAL",
            finding_id=self.finding.id,
            alert_id=alert.id,
            asset_id=self.asset.id,
        )

        self.assertIsNotNone(incident.id)
        self.assertEqual(incident.status, "OPEN")
        self.assertEqual(incident.alert_id, alert.id)

        # Creating an incident resolves the source alert.
        self.assertEqual(alert.status, "RESOLVED")

        updated = update_incident(
            self.db,
            incident,
            status="INVESTIGATING",
            actor=self.user,
        )

        self.assertEqual(updated.status, "INVESTIGATING")

    def test_list_incidents_filter(self) -> None:
        create_incident(
            self.db,
            user_id=self.user_id,
            title="Sample incident",
            severity="MEDIUM",
        )

        result = list_incidents(
            self.db,
            self.user_id,
            severity="MEDIUM",
        )

        self.assertEqual(result["total"], 1)
        self.assertEqual(result["open"], 1)

    def test_incident_isolation(self) -> None:
        other = User(
            username="other",
            email="other2@example.com",
            password_hash="unused",
            role=UserRole.USER,
            is_active=True,
        )
        self.db.add(other)
        self.db.commit()

        incident = create_incident(
            self.db,
            user_id=self.user_id,
            title="Secret",
            severity="HIGH",
        )

        self.assertIsNone(
            get_incident(self.db, incident.id, other.id)
        )
        self.assertEqual(
            list_incidents(self.db, other.id)["total"],
            0,
        )


if __name__ == "__main__":
    unittest.main()