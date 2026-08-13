"""Tests for the Threat Intelligence platform module."""

import unittest
from unittest import mock

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.exceptions import ValidationError
from app.database import models  # noqa: F401 - register mapped models
from app.database.base import Base
from app.intelligence import service
from app.intelligence.cache import clear_cache
from app.intelligence.providers import virustotal
from app.intelligence.schemas import IOCType, ThreatLevel
from app.integrations.virustotal.exceptions import VirusTotalNotConfiguredError
from app.models.intelligence_search import IntelligenceSearch
from app.models.user import User
from app.services.integration_credentials import upsert_api_key
from app.services.intelligence_service import enrich_service

_API_KEY = "intelligence-test-api-key"

_ENRICHED_POSTGRES_CPE = (
    "cpe:2.3:a:postgresql:postgresql:16.4:*:*:*:*:*:*:*"
)


def _raw_vuln(criteria: str) -> dict:
    return {
        "cve": {
            "id": "CVE-2024-0001",
            "configurations": [
                {
                    "nodes": [
                        {"cpeMatch": [{"criteria": criteria, "vulnerable": True}]}
                    ]
                }
            ],
        }
    }


def _raw_ip_report(
    *,
    malicious: int = 2,
    suspicious: int = 0,
    harmless: int = 10,
    undetected: int = 5,
    reputation: int = -10,
    tags: list[str] | None = None,
    asn: int = 15169,
    country: str = "US",
) -> dict:
    return {
        "data": {
            "id": "8.8.8.8",
            "type": "ip_address",
            "attributes": {
                "asn": asn,
                "as_owner": "GOOGLE",
                "country": country,
                "regional_internet_registry": "ARIN",
                "reputation": reputation,
                "last_analysis_stats": {
                    "malicious": malicious,
                    "suspicious": suspicious,
                    "undetected": undetected,
                    "harmless": harmless,
                    "timeout": 0,
                    "confirmed-timeout": 0,
                    "failure": 0,
                    "type-unsupported": 0,
                },
                "last_analysis_results": {
                    "VendorA": {
                        "category": "malicious",
                        "result": "Botnet",
                        "engine_name": "VendorA",
                        "engine_version": "1.0",
                    },
                    "VendorB": {
                        "category": "clean",
                        "result": "clean",
                        "engine_name": "VendorB",
                    },
                },
                "last_analysis_date": 1700000000,
                "first_seen_date": 1600000000,
                "total_votes": {"malicious": 8, "harmless": 3},
                "tags": tags or ["botnet", "c2"],
                "categories": {"AVG": "malicious"},
            },
        }
    }


class IocDetectionTests(unittest.TestCase):
    def test_detects_url(self) -> None:
        self.assertEqual(
            service.detect_ioc_type("https://example.com/page"),
            IOCType.URL,
        )

    def test_detects_sha256_hash(self) -> None:
        self.assertEqual(service.detect_ioc_type("a" * 64), IOCType.HASH)

    def test_detects_ipv4_and_ipv6(self) -> None:
        self.assertEqual(service.detect_ioc_type("8.8.8.8"), IOCType.IP)
        self.assertEqual(service.detect_ioc_type("::1"), IOCType.IP)

    def test_detects_domain(self) -> None:
        self.assertEqual(service.detect_ioc_type("example.com"), IOCType.DOMAIN)

    def test_accepts_whitespace(self) -> None:
        self.assertEqual(service.detect_ioc_type("  1.1.1.1  "), IOCType.IP)

    def test_rejects_unknown_value(self) -> None:
        with self.assertRaises(ValidationError):
            service.detect_ioc_type("not an ioc!!")

    def test_rejects_empty_value(self) -> None:
        with self.assertRaises(ValidationError):
            service.detect_ioc_type("   ")


class ProviderNormalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        clear_cache()

    def tearDown(self) -> None:
        clear_cache()

    def test_normalizes_report_fully(self) -> None:
        with mock.patch(
            "app.intelligence.providers.virustotal._get",
            return_value=_raw_ip_report(),
        ):
            report = virustotal.lookup(_API_KEY, IOCType.IP, "8.8.8.8")

        self.assertTrue(report.found)
        self.assertTrue(report.detected)
        self.assertEqual(report.threat_level, ThreatLevel.CRITICAL)
        self.assertEqual(report.risk_score, 78)
        self.assertGreater(report.risk_score, 0)
        self.assertEqual(report.asn, "AS15169")
        self.assertEqual(report.as_owner, "GOOGLE")
        self.assertEqual(report.country, "US")
        self.assertEqual(report.registrar, "ARIN")
        self.assertEqual(report.detection_ratio, "2/17")
        self.assertEqual(report.submission_count, 0)
        self.assertEqual(report.community_votes.malicious, 8)
        self.assertIsNotNone(report.first_seen)
        self.assertIn("T1071", [m.technique_id for m in report.mitre])
        self.assertEqual(len(report.vendor_detections), 2)
        self.assertEqual(report.vendor_detections[0].engine, "VendorA")

    def test_clean_report_maps_to_clean_threat_level(self) -> None:
        raw = _raw_ip_report(malicious=0, suspicious=0, reputation=50, tags=["legit"])
        raw["data"]["attributes"]["categories"] = {"AVG": "search-engine"}

        with mock.patch(
            "app.intelligence.providers.virustotal._get",
            return_value=raw,
        ):
            report = virustotal.lookup(_API_KEY, IOCType.IP, "8.8.8.8")

        self.assertFalse(report.detected)
        self.assertEqual(report.threat_level, ThreatLevel.CLEAN)
        self.assertEqual(report.mitre, [])

    def test_critical_risk_for_high_detection(self) -> None:
        raw = _raw_ip_report(malicious=5, reputation=-100)

        with mock.patch(
            "app.intelligence.providers.virustotal._get",
            return_value=raw,
        ):
            report = virustotal.lookup(_API_KEY, IOCType.IP, "8.8.8.8")

        self.assertEqual(report.threat_level, ThreatLevel.CRITICAL)
        self.assertEqual(report.risk_score, 100)

    def test_not_found_report(self) -> None:
        with mock.patch(
            "app.intelligence.providers.virustotal._get",
            return_value=None,
        ):
            report = virustotal.lookup(_API_KEY, IOCType.DOMAIN, "ghost.example.com")

        self.assertFalse(report.found)
        self.assertEqual(report.threat_level, ThreatLevel.UNKNOWN)
        self.assertFalse(report.detected)

    def test_domain_derives_registrar_and_creation(self) -> None:
        raw = {
            "data": {
                "id": "example.com",
                "type": "domain",
                "attributes": {
                    "registrar": "MarkMonitor",
                    "creation_date": 1356998400,
                    "whois": "Registrant Country: US",
                    "reputation": 0,
                    "last_analysis_stats": {
                        "malicious": 0,
                        "suspicious": 0,
                        "undetected": 0,
                        "harmless": 5,
                        "timeout": 0,
                        "confirmed-timeout": 0,
                        "failure": 0,
                        "type-unsupported": 0,
                    },
                    "last_analysis_results": {},
                    "categories": {},
                    "tags": [],
                },
            }
        }

        with mock.patch(
            "app.intelligence.providers.virustotal._get",
            return_value=raw,
        ):
            report = virustotal.lookup(_API_KEY, IOCType.DOMAIN, "example.com")

        self.assertTrue(report.found)
        self.assertEqual(report.registrar, "MarkMonitor")
        self.assertEqual(report.country, "US")
        self.assertIsNotNone(report.creation_date)

    def test_cache_serves_second_lookup(self) -> None:
        with mock.patch(
            "app.intelligence.providers.virustotal._get",
            return_value=_raw_ip_report(),
        ) as mocked:
            first = virustotal.lookup(_API_KEY, IOCType.IP, "8.8.8.8")
            second = virustotal.lookup(_API_KEY, IOCType.IP, "8.8.8.8")

        mocked.assert_called_once()
        self.assertFalse(first.from_cache)
        self.assertTrue(second.from_cache)

    def test_hash_is_normalized_lowercase_for_cache(self) -> None:
        value = "A" * 64

        with mock.patch(
            "app.intelligence.providers.virustotal._get",
            return_value=_raw_ip_report(),
        ) as mocked:
            first = virustotal.lookup(_API_KEY, IOCType.HASH, value)
            second = virustotal.lookup(_API_KEY, IOCType.HASH, value.lower())

        mocked.assert_called_once()
        self.assertEqual(first.resource, value.lower())
        self.assertTrue(second.from_cache)


class HistoryServiceTests(unittest.TestCase):
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
        clear_cache()
        self.db: Session = self.session_factory()
        self.user = User(
            username="inteluser",
            email="inteluser@example.com",
            password_hash="unused",
            is_active=True,
        )
        self.db.add(self.user)
        self.db.commit()
        self.db.refresh(self.user)
        upsert_api_key(self.db, self.user.id, "virustotal", _API_KEY)

    def tearDown(self) -> None:
        clear_cache()
        self.db.close()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def test_lookup_records_history(self) -> None:
        with mock.patch(
            "app.intelligence.providers.virustotal._get",
            return_value=_raw_ip_report(),
        ):
            response = service.lookup(self.db, self.user.id, "8.8.8.8")

        self.assertIsNotNone(response.history_id)
        self.assertTrue(response.report.found)

        row = (
            self.db.query(IntelligenceSearch)
            .filter(IntelligenceSearch.id == response.history_id)
            .first()
        )
        self.assertIsNotNone(row)
        self.assertEqual(row.resource_type, "ip")
        self.assertEqual(row.resource, "8.8.8.8")

    def test_lookup_requires_configured_key(self) -> None:
        with mock.patch(
            "app.intelligence.providers.virustotal._get",
            return_value=_raw_ip_report(),
        ):
            with self.assertRaises(VirusTotalNotConfiguredError):
                # Use a second user with no configured key.
                other = User(
                    username="inteluser2",
                    email="inteluser2@example.com",
                    password_hash="unused",
                    is_active=True,
                )
                self.db.add(other)
                self.db.commit()
                self.db.refresh(other)
                service.lookup(self.db, other.id, "8.8.8.8")

    def test_history_listing_filters_by_type(self) -> None:
        def _lookup(value: str) -> None:
            raw = _raw_ip_report()
            raw["data"]["id"] = value
            with mock.patch(
                "app.intelligence.providers.virustotal._get",
                return_value=raw,
            ):
                service.lookup(self.db, self.user.id, value)

        _lookup("8.8.8.8")
        _lookup("1.1.1.1")

        result = service.list_history(
            self.db,
            self.user.id,
            ioc_type=IOCType.IP,
        )
        self.assertEqual(result.total, 2)

        result = service.list_history(
            self.db,
            self.user.id,
            ioc_type=IOCType.DOMAIN,
        )
        self.assertEqual(result.total, 0)

    def test_history_listing_searches_resource(self) -> None:
        with mock.patch(
            "app.intelligence.providers.virustotal._get",
            return_value=_raw_ip_report(),
        ):
            service.lookup(self.db, self.user.id, "10.10.10.10")

        result = service.list_history(self.db, self.user.id, query="10.10")
        self.assertEqual(result.total, 1)

    def test_delete_history_is_user_scoped(self) -> None:
        with mock.patch(
            "app.intelligence.providers.virustotal._get",
            return_value=_raw_ip_report(),
        ):
            response = service.lookup(self.db, self.user.id, "8.8.8.8")

        other = User(
            username="inteluser3",
            email="inteluser3@example.com",
            password_hash="unused",
            is_active=True,
        )
        self.db.add(other)
        self.db.commit()
        self.db.refresh(other)

        self.assertFalse(service.delete_history(self.db, other.id, response.history_id or -1))
        self.assertTrue(service.delete_history(self.db, self.user.id, response.history_id or -1))

    def test_clear_history_removes_all(self) -> None:
        with mock.patch(
            "app.intelligence.providers.virustotal._get",
            return_value=_raw_ip_report(),
        ):
            service.lookup(self.db, self.user.id, "8.8.8.8")
            service.lookup(self.db, self.user.id, "1.1.1.1")

        deleted = service.clear_history(self.db, self.user.id)
        self.assertEqual(deleted, 2)

        result = service.list_history(self.db, self.user.id)
        self.assertEqual(result.total, 0)

    def test_status_reflects_configuration(self) -> None:
        self.assertTrue(service.status(self.db, self.user.id).configured)


class ServiceEnrichmentTests(unittest.TestCase):

    def test_enriches_known_product(self) -> None:
        with mock.patch(
            "app.services.intelligence_service.get_cves_by_cpe",
            return_value=[_raw_vuln(_ENRICHED_POSTGRES_CPE)],
        ) as mocked:
            result = enrich_service("PostgreSQL DB", "16.4")

        self.assertEqual(result["product"], "postgresql")
        self.assertEqual(result["cpe"], _ENRICHED_POSTGRES_CPE)
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["cves"][0]["cve"]["id"], "CVE-2024-0001")
        mocked.assert_called_once_with(_ENRICHED_POSTGRES_CPE)

    def test_skips_nvd_lookup_when_no_cpe(self) -> None:
        with mock.patch(
            "app.services.intelligence_service.get_cves_by_cpe",
        ) as mocked:
            result = enrich_service(None, None)

        mocked.assert_not_called()
        self.assertIsNone(result["cpe"])
        self.assertEqual(result["count"], 0)


if __name__ == "__main__":
    unittest.main()
