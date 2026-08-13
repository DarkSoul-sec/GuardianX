"""Tests for the VirusTotal Intelligence integration."""

import unittest
from unittest import mock

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.encryption import decrypt_secret
from app.core.exceptions import ValidationError
from app.database import models  # noqa: F401 - register mapped models
from app.database.base import Base
from app.integrations.virustotal import (
    connect_api_key,
    disconnect_api_key,
    get_status,
    lookup_domain,
    lookup_file_hash,
    lookup_ip,
    lookup_url,
    test_connection as validate_connection,
)
from app.integrations.virustotal.exceptions import (
    VirusTotalError,
    VirusTotalInvalidKeyError,
    VirusTotalNotConfiguredError,
    VirusTotalRateLimitError,
)
from app.integrations.virustotal.schemas import (
    IntegrationStatus,
    VirusTotalConnectionStatus,
)
from app.integrations.virustotal.service import (
    _CACHE,
    get_configured_api_key,
)
from app.models.integration_credential import IntegrationCredential
from app.models.user import User

_API_KEY = "test-virustotal-api-key"


def _raw_report(
    *,
    malicious: int = 1,
    suspicious: int = 0,
    undetected: int = 3,
    harmless: int = 4,
    timeout: int = 0,
    reputation: int = -2,
    popular_threat_category: str | None = None,
) -> dict:
    return {
        "data": {
            "id": "sample",
            "type": "file",
            "attributes": {
                "last_analysis_stats": {
                    "malicious": malicious,
                    "suspicious": suspicious,
                    "undetected": undetected,
                    "harmless": harmless,
                    "timeout": timeout,
                    "confirmed-timeout": 0,
                    "failure": 0,
                    "type-unsupported": 0,
                },
                "last_analysis_results": {
                    "VendorA": {
                        "category": "malicious",
                        "result": "Trojan.Generic",
                        "method": "blacklist",
                        "engine_name": "VendorA",
                    },
                    "VendorB": {
                        "category": "clean",
                        "result": "clean",
                        "method": "blacklist",
                        "engine_name": "VendorB",
                    },
                },
                "last_analysis_date": 1700000000,
                "reputation": reputation,
                "meaningful_name": "evil.exe",
                "type_description": "PE32 executable",
                "popular_threat_category": popular_threat_category,
                "categories": {},
                "tags": ["pe32"],
            },
        }
    }


class VirusTotalTests(unittest.TestCase):

    def setUp(self) -> None:
        _CACHE.clear()

    def tearDown(self) -> None:
        _CACHE.clear()

    # ------------------------------------------------------------------
    # Input validation
    # ------------------------------------------------------------------

    def test_lookup_url_rejects_non_http_url(self) -> None:
        with self.assertRaises(ValidationError):
            lookup_url(_API_KEY, "not-a-url")

    def test_lookup_domain_rejects_invalid_domain(self) -> None:
        with self.assertRaises(ValidationError):
            lookup_domain(_API_KEY, "bad domain!!")

    def test_lookup_ip_rejects_invalid_ip(self) -> None:
        with self.assertRaises(ValidationError):
            lookup_ip(_API_KEY, "999.999.1.1")

    def test_lookup_file_hash_rejects_bad_hash(self) -> None:
        with self.assertRaises(ValidationError):
            lookup_file_hash(_API_KEY, "abc123")

    # ------------------------------------------------------------------
    # Mapping
    # ------------------------------------------------------------------

    def test_lookup_maps_analysis_stats(self) -> None:
        with mock.patch(
            "app.integrations.virustotal.service._get",
            return_value=_raw_report(),
        ):
            response = lookup_file_hash(
                _API_KEY,
                "0" * 64,
            )

        self.assertTrue(response.found)
        self.assertTrue(response.detected)
        self.assertEqual(response.malicious, 1)
        self.assertEqual(response.suspicious, 0)
        self.assertEqual(response.undetected, 3)
        self.assertEqual(response.harmless, 4)
        self.assertEqual(response.total, 8)
        self.assertEqual(response.detection_ratio, "1/8")
        self.assertEqual(response.reputation, -2)
        self.assertEqual(response.community_score, -2)
        self.assertIsNotNone(response.last_analysis_date)

    def test_lookup_maps_vendor_detections(self) -> None:
        with mock.patch(
            "app.integrations.virustotal.service._get",
            return_value=_raw_report(),
        ):
            response = lookup_file_hash(_API_KEY, "f" * 64)

        self.assertEqual(len(response.vendor_detections), 2)
        first = response.vendor_detections[0]
        self.assertEqual(first.engine, "VendorA")
        self.assertEqual(first.category, "malicious")
        self.assertEqual(first.result, "Trojan.Generic")

    def test_lookup_uses_popular_threat_category_for_files(self) -> None:
        with mock.patch(
            "app.integrations.virustotal.service._get",
            return_value=_raw_report(popular_threat_category="Trojan"),
        ):
            response = lookup_file_hash(_API_KEY, "a" * 64)

        self.assertEqual(response.threat_category, "Trojan")

    def test_lookup_uses_categories_for_domains(self) -> None:
        raw = _raw_report()
        raw["data"]["type"] = "domain"
        raw["data"]["attributes"]["categories"] = {"AVG": "phishing"}
        raw["data"]["attributes"]["popular_threat_category"] = None

        with mock.patch(
            "app.integrations.virustotal.service._get",
            return_value=raw,
        ):
            response = lookup_domain(_API_KEY, "example.com")

        self.assertEqual(response.threat_category, "phishing")

    def test_lookup_builds_permalink_for_url(self) -> None:
        with mock.patch(
            "app.integrations.virustotal.service._get",
            return_value=_raw_report(),
        ):
            response = lookup_url(_API_KEY, "https://example.com/page")

        self.assertTrue(response.permalink.startswith("https://www.virustotal.com/gui/url/"))

    def test_lookup_builds_permalink_for_file(self) -> None:
        with mock.patch(
            "app.integrations.virustotal.service._get",
            return_value=_raw_report(),
        ):
            response = lookup_file_hash(_API_KEY, "b" * 64)

        self.assertEqual(
            response.permalink,
            f"https://www.virustotal.com/gui/file/{'b' * 64}",
        )

    def test_lookup_returns_not_found_on_404(self) -> None:
        with mock.patch(
            "app.integrations.virustotal.service._get",
            return_value=None,
        ):
            response = lookup_domain(_API_KEY, "unknown.example.com")

        self.assertFalse(response.found)
        self.assertFalse(response.detected)
        self.assertEqual(response.total, 0)
        self.assertEqual(response.vendor_detections, [])

    def test_lookup_not_detected_when_clean(self) -> None:
        with mock.patch(
            "app.integrations.virustotal.service._get",
            return_value=_raw_report(
                malicious=0,
                suspicious=0,
                undetected=0,
                harmless=8,
            ),
        ):
            response = lookup_file_hash(_API_KEY, "c" * 64)

        self.assertFalse(response.detected)
        self.assertEqual(response.detection_ratio, "0/8")

    def test_lookup_surfaces_transport_errors(self) -> None:
        with mock.patch(
            "app.integrations.virustotal.service._get",
            side_effect=VirusTotalError("API down"),
        ):
            with self.assertRaises(VirusTotalError):
                lookup_ip(_API_KEY, "8.8.8.8")

    # ------------------------------------------------------------------
    # Caching
    # ------------------------------------------------------------------

    def test_lookup_uses_cache(self) -> None:
        with mock.patch(
            "app.integrations.virustotal.service._get",
            return_value=_raw_report(),
        ) as mocked:
            lookup_file_hash(_API_KEY, "d" * 64)
            lookup_file_hash(_API_KEY, "d" * 64)

        mocked.assert_called_once()

    def test_lookup_caches_not_found(self) -> None:
        with mock.patch(
            "app.integrations.virustotal.service._get",
            return_value=None,
        ) as mocked:
            lookup_domain(_API_KEY, "cached.example.com")
            lookup_domain(_API_KEY, "cached.example.com")

        mocked.assert_called_once()

    def test_lookup_miss_after_clear(self) -> None:
        with mock.patch(
            "app.integrations.virustotal.service._get",
            return_value=_raw_report(),
        ) as mocked:
            lookup_file_hash(_API_KEY, "e" * 64)
            _CACHE.clear()
            lookup_file_hash(_API_KEY, "e" * 64)

        self.assertEqual(mocked.call_count, 2)


class ConnectionTestTests(unittest.TestCase):

    def test_reports_connected_on_success(self) -> None:
        with mock.patch(
            "app.integrations.virustotal.service._get",
            return_value=_raw_report(),
        ):
            result = validate_connection("valid-key-1234567890")

        self.assertIsInstance(result, VirusTotalConnectionStatus)
        self.assertEqual(result.status, "connected")

    def test_reports_invalid_key(self) -> None:
        with mock.patch(
            "app.integrations.virustotal.service._get",
            side_effect=VirusTotalInvalidKeyError(),
        ):
            result = validate_connection("bad-key")

        self.assertEqual(result.status, "invalid")

    def test_reports_rate_limited(self) -> None:
        with mock.patch(
            "app.integrations.virustotal.service._get",
            side_effect=VirusTotalRateLimitError(),
        ):
            result = validate_connection("throttled-key")

        self.assertEqual(result.status, "rate_limited")

    def test_reports_unreachable(self) -> None:
        with mock.patch(
            "app.integrations.virustotal.service._get",
            side_effect=VirusTotalError("network down"),
        ):
            result = validate_connection("any-key")

        self.assertEqual(result.status, "unreachable")


class CredentialStoreTests(unittest.TestCase):
    """BYOAPI credential persistence through the service layer."""

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
        self.user = User(
            username="vtuser",
            email="vtuser@example.com",
            password_hash="unused",
            is_active=True,
        )
        self.db.add(self.user)
        self.db.commit()
        self.db.refresh(self.user)

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def test_connect_encrypts_key_at_rest(self) -> None:
        plaintext = "a" * 64

        with mock.patch(
            "app.integrations.virustotal.service._get",
            return_value=_raw_report(),
        ):
            status = connect_api_key(self.db, self.user.id, plaintext)

        self.assertEqual(status.status, "connected")

        row = (
            self.db.query(IntegrationCredential)
            .filter(IntegrationCredential.user_id == self.user.id)
            .first()
        )
        self.assertIsNotNone(row)
        self.assertNotEqual(row.encrypted_api_key, plaintext)
        self.assertNotIn(plaintext, row.encrypted_api_key)
        self.assertEqual(decrypt_secret(row.encrypted_api_key), plaintext)

    def test_connect_persists_failed_test_status(self) -> None:
        with mock.patch(
            "app.integrations.virustotal.service._get",
            side_effect=VirusTotalInvalidKeyError(),
        ):
            status = connect_api_key(self.db, self.user.id, "b" * 64)

        self.assertEqual(status.status, "invalid")
        self.assertTrue(status.configured)

    def test_status_returns_not_configured_by_default(self) -> None:
        status = get_status(self.db, self.user.id)

        self.assertIsInstance(status, IntegrationStatus)
        self.assertFalse(status.configured)
        self.assertEqual(status.status, "not_configured")

    def test_disconnect_removes_stored_key(self) -> None:
        with mock.patch(
            "app.integrations.virustotal.service._get",
            return_value=_raw_report(),
        ):
            connect_api_key(self.db, self.user.id, "c" * 64)

        self.assertTrue(disconnect_api_key(self.db, self.user.id))
        self.assertEqual(
            get_status(self.db, self.user.id).status,
            "not_configured",
        )

    def test_get_configured_api_key_raises_when_missing(self) -> None:
        with self.assertRaises(VirusTotalNotConfiguredError):
            get_configured_api_key(self.db, self.user.id)

    def test_stored_key_never_appears_in_status_response(self) -> None:
        with mock.patch(
            "app.integrations.virustotal.service._get",
            return_value=_raw_report(),
        ):
            connect_api_key(self.db, self.user.id, "d" * 64)

        status = get_status(self.db, self.user.id)
        payload = status.model_dump()
        self.assertNotIn("d" * 64, str(payload))


if __name__ == "__main__":
    unittest.main()
