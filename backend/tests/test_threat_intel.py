"""Tests for the Threat Intelligence Center module."""

import unittest
from unittest import mock

from app.core.exceptions import ResourceNotFoundError
from app.integrations.threat_intel import (
    get_attack_techniques,
    get_cve_detail,
    get_kev_catalog,
    get_stats,
    get_trending,
    search_cves,
)
from app.integrations.threat_intel.nvd import _normalize_entry


def _nvd_entry(
    cve_id: str = "CVE-2024-0001",
    score: float | None = 9.8,
    published: str = "2024-01-15T10:00:00.000",
    cwes: list[str] | None = None,
    vendor: str = "apache",
    references: list[dict] | None = None,
) -> dict:
    metrics = {}
    if score is not None:
        metrics["cvssMetricV31"] = [{"cvssData": {"baseScore": score}}]

    return {
        "cve": {
            "id": cve_id,
            "descriptions": [
                {
                    "lang": "en",
                    "value": "Vulnerability in the product. Remote code execution.",
                }
            ],
            "metrics": metrics,
            "published": published,
            "lastModified": "2024-02-01T00:00:00.000",
            "weaknesses": [
                {
                    "description": [
                        {"lang": "en", "value": cwe} for cwe in (cwes or [])
                    ]
                }
            ],
            "configurations": [
                {
                    "nodes": [
                        {
                            "cpeMatch": [
                                {
                                    "criteria": (
                                        f"cpe:2.3:a:{vendor}:product:*:"
                                        "*:*:*:*:*:*:*"
                                    )
                                }
                            ]
                        }
                    ]
                }
            ],
            "references": references
            or [
                {
                    "url": "https://vendor.example.com/advisory",
                    "source": "vendor",
                    "tags": ["Vendor Advisory"],
                }
            ],
        }
    }


def _cve(
    cve_id: str = "CVE-2024-0001",
    severity: str = "CRITICAL",
    published: str = "2024-01-15T10:00:00.000",
    cwes: list[str] | None = None,
    score: float | None = 0.9,
) -> dict:
    return {
        "id": cve_id,
        "title": f"Title {cve_id}",
        "description": f"Description {cve_id}",
        "severity": severity,
        "cvss_score": 9.8,
        "published": published,
        "last_modified": "2024-02-01T00:00:00.000",
        "vendor": "apache",
        "cwes": cwes or ["CWE-89"],
        "references": [],
    }


class NvdNormalizationTests(unittest.TestCase):

    def test_normalizes_score_and_severity(self) -> None:
        result = _normalize_entry(_nvd_entry(score=9.8))
        self.assertEqual(result["id"], "CVE-2024-0001")
        self.assertEqual(result["severity"], "CRITICAL")
        self.assertEqual(result["cvss_score"], 9.8)

    def test_severity_bands(self) -> None:
        self.assertEqual(_normalize_entry(_nvd_entry(score=9.0))["severity"], "CRITICAL")
        self.assertEqual(_normalize_entry(_nvd_entry(score=7.0))["severity"], "HIGH")
        self.assertEqual(_normalize_entry(_nvd_entry(score=4.0))["severity"], "MEDIUM")
        self.assertEqual(_normalize_entry(_nvd_entry(score=3.9))["severity"], "LOW")
        self.assertEqual(_normalize_entry(_nvd_entry(score=None))["severity"], "UNKNOWN")

    def test_extracts_cwes_vendor_and_references(self) -> None:
        result = _normalize_entry(
            _nvd_entry(
                cwes=["CWE-79", "CWE-89"],
                vendor="microsoft",
            )
        )
        self.assertEqual(result["cwes"], ["CWE-79", "CWE-89"])
        self.assertEqual(result["vendor"], "microsoft")
        self.assertEqual(result["references"][0]["url"], "https://vendor.example.com/advisory")


class ThreatIntelServiceTests(unittest.TestCase):

    def setUp(self) -> None:
        self.cves = [
            _cve("CVE-2024-0001", "CRITICAL", "2024-01-15T10:00:00.000"),
            _cve("CVE-2024-0002", "HIGH", "2024-01-14T10:00:00.000"),
            _cve("CVE-2024-0003", "LOW", "2024-01-13T10:00:00.000"),
        ]

    def test_get_trending_enriches_and_sorts(self) -> None:
        with (
            mock.patch(
                "app.integrations.threat_intel.nvd.search_cves",
                return_value=list(self.cves),
            ),
            mock.patch(
                "app.integrations.threat_intel.epss.get_epss_scores",
                return_value={
                    "CVE-2024-0001": {"score": 0.9, "percentile": 98.0},
                },
            ),
            mock.patch(
                "app.integrations.threat_intel.kev.get_kev_catalog",
                return_value=[
                    {
                        "cve_id": "CVE-2024-0002",
                        "vendor": "x",
                        "product": "y",
                        "vulnerability_name": "z",
                        "description": "d",
                        "required_action": "apply patch",
                        "due_date": "2024-06-01",
                        "date_added": "2024-03-01",
                        "known_ransomware_campaign": True,
                    }
                ],
            ),
        ):
            response = get_trending(days=14, limit=10)

        self.assertEqual(response["total"], 3)
        self.assertEqual(
            [item["id"] for item in response["items"]],
            ["CVE-2024-0001", "CVE-2024-0002", "CVE-2024-0003"],
        )
        self.assertEqual(response["items"][0]["epss_score"], 0.9)
        self.assertTrue(response["items"][1]["exploited"])
        self.assertFalse(response["items"][0]["exploited"])

    def test_search_cves_filters_exploited_only(self) -> None:
        with (
            mock.patch(
                "app.integrations.threat_intel.nvd.search_cves",
                return_value=list(self.cves),
            ),
            mock.patch(
                "app.integrations.threat_intel.epss.get_epss_scores",
                return_value={},
            ),
            mock.patch(
                "app.integrations.threat_intel.kev.get_kev_catalog",
                return_value=[
                    {
                        "cve_id": "CVE-2024-0002",
                        "vendor": "x",
                        "product": "y",
                        "vulnerability_name": "z",
                        "description": "d",
                        "required_action": "a",
                        "due_date": "2024-06-01",
                        "date_added": "2024-03-01",
                        "known_ransomware_campaign": False,
                    }
                ],
            ),
        ):
            response = search_cves(
                query="apache",
                severity="CRITICAL",
                exploited_only=True,
                limit=20,
            )

        self.assertEqual(response["exploited_only"], True)
        self.assertEqual(response["total"], 1)
        self.assertEqual(response["items"][0]["id"], "CVE-2024-0002")

    def test_get_cve_detail_includes_attack_and_advisories(self) -> None:
        cve = _cve(cwes=["CWE-89"])
        cve["references"] = [
            {
                "url": "https://vendor.example.com/advisory",
                "source": "vendor",
                "tags": ["Vendor Advisory"],
            },
            {
                "url": "https://example.com/misc",
                "source": "misc",
                "tags": [],
            },
        ]

        with (
            mock.patch(
                "app.integrations.threat_intel.nvd.get_cve",
                return_value=dict(cve),
            ),
            mock.patch(
                "app.integrations.threat_intel.epss.get_epss_scores",
                return_value={"CVE-2024-0001": {"score": 0.5, "percentile": 80.0}},
            ),
            mock.patch(
                "app.integrations.threat_intel.kev.get_kev_catalog",
                return_value=[],
            ),
        ):
            detail = get_cve_detail("CVE-2024-0001")

        self.assertEqual(detail["id"], "CVE-2024-0001")
        self.assertEqual(detail["epss_score"], 0.5)
        self.assertEqual(len(detail["attack_techniques"]), 2)
        self.assertEqual(
            [t["id"] for t in detail["attack_techniques"]],
            ["T1190", "T1059"],
        )
        self.assertEqual(len(detail["advisories"]), 1)
        self.assertEqual(detail["advisories"][0]["source"], "vendor")

    def test_get_cve_detail_unknown_raises(self) -> None:
        with mock.patch(
            "app.integrations.threat_intel.nvd.get_cve",
            return_value=None,
        ):
            with self.assertRaises(ResourceNotFoundError):
                get_cve_detail("CVE-2099-0000")

    def test_get_stats_builds_distributions_and_timeline(self) -> None:
        from datetime import UTC, datetime, timedelta

        today = datetime.now(UTC).date()
        d0 = today.isoformat()
        d1 = (today - timedelta(days=1)).isoformat()
        d2 = (today - timedelta(days=2)).isoformat()

        timeline_cves = [
            _cve("CVE-2024-0001", "CRITICAL", f"{d0}T10:00:00.000"),
            _cve("CVE-2024-0002", "HIGH", f"{d1}T10:00:00.000"),
            _cve("CVE-2024-0003", "LOW", f"{d2}T10:00:00.000"),
            _cve(
                "CVE-2024-0004",
                "CRITICAL",
                f"{d0}T11:00:00.000",
                score=0.9,
            ),
            _cve(
                "CVE-2024-0005",
                "MEDIUM",
                f"{today.isoformat()}T09:00:00.000",
                score=0.2,
            ),
        ]

        with (
            mock.patch(
                "app.integrations.threat_intel.nvd.search_cves",
                return_value=timeline_cves,
            ),
            mock.patch(
                "app.integrations.threat_intel.epss.get_epss_scores",
                return_value={
                    "CVE-2024-0001": {"score": 0.9, "percentile": 98.0},
                    "CVE-2024-0002": {"score": 0.05, "percentile": 20.0},
                    "CVE-2024-0004": {"score": 0.9, "percentile": 98.0},
                    "CVE-2024-0005": {"score": 0.2, "percentile": 60.0},
                },
            ),
            mock.patch(
                "app.integrations.threat_intel.kev.get_kev_catalog",
                return_value=[],
            ),
            mock.patch(
                "app.integrations.threat_intel.nvd.is_healthy",
                return_value=True,
            ),
            mock.patch(
                "app.integrations.threat_intel.kev.is_healthy",
                return_value=True,
            ),
            mock.patch(
                "app.integrations.threat_intel.epss.is_healthy",
                return_value=True,
            ),
        ):
            stats = get_stats(days=14)

        self.assertEqual(stats["total_cves"], 5)
        self.assertEqual(stats["critical"], 2)
        self.assertEqual(stats["high"], 1)
        self.assertEqual(stats["medium"], 1)
        self.assertEqual(stats["low"], 1)

        severity_map = {
            item["severity"]: item["count"]
            for item in stats["severity_distribution"]
        }
        self.assertEqual(severity_map["CRITICAL"], 2)

        epss_map = {
            item["bucket"]: item["count"]
            for item in stats["epss_distribution"]
        }
        self.assertEqual(epss_map["Very High (>70%)"], 2)

        timeline = stats["risk_timeline"]
        self.assertGreaterEqual(len(timeline), 3)
        jan_15 = next(
            (point for point in timeline if point["date"].endswith(d0)),
            None,
        )
        self.assertIsNotNone(jan_15)
        self.assertEqual(jan_15["published_count"], 3)

        sources = {source["source"]: source for source in stats["sources"]}
        self.assertEqual(
            set(sources.keys()),
            {"nvd", "cisa_kev", "epss", "mitre_attck"},
        )
        self.assertTrue(all(source["healthy"] for source in sources.values()))

    def test_get_kev_catalog_sorts_most_recent_first(self) -> None:
        entries = [
            {
                "cve_id": "CVE-2024-0001",
                "vendor": "a",
                "product": "b",
                "vulnerability_name": "c",
                "description": "d",
                "required_action": "e",
                "due_date": "2024-01-01",
                "date_added": "2024-01-10",
                "known_ransomware_campaign": False,
            },
            {
                "cve_id": "CVE-2024-0002",
                "vendor": "a",
                "product": "b",
                "vulnerability_name": "c",
                "description": "d",
                "required_action": "e",
                "due_date": "2024-01-01",
                "date_added": "2024-02-10",
                "known_ransomware_campaign": True,
            },
        ]

        with mock.patch(
            "app.integrations.threat_intel.kev.get_kev_catalog",
            return_value=entries,
        ):
            result = get_kev_catalog(limit=10)

        self.assertEqual(result[0]["cve_id"], "CVE-2024-0002")

    def test_get_attack_techniques_filters_by_tactic(self) -> None:
        execution = get_attack_techniques(tactic="execution")
        self.assertTrue(all(
            "Execution" in technique["tactics"] for technique in execution
        ))
        all_techniques = get_attack_techniques()
        self.assertGreater(len(all_techniques), len(execution))


if __name__ == "__main__":
    unittest.main()
