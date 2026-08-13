"""Tests for NVD vulnerability filtering by product match."""

import unittest

from app.services.cve_filter import filter_cves

POSTGRES_CPE = "cpe:2.3:a:postgresql:postgresql:*:*:*:*:*:*:*"
MYSQL_CPE = "cpe:2.3:a:oracle:mysql:*:*:*:*:*:*:*"


def _vuln(criteria: str, vulnerable: bool = True) -> dict:
    return {
        "cve": {
            "configurations": [
                {
                    "nodes": [
                        {
                            "cpeMatch": [
                                {"criteria": criteria, "vulnerable": vulnerable}
                            ]
                        }
                    ]
                }
            ]
        }
    }


class FilterCvesTests(unittest.TestCase):

    def test_keeps_matching_vendor_or_product(self) -> None:
        filtered = filter_cves(
            [_vuln(POSTGRES_CPE), _vuln(MYSQL_CPE)],
            "postgresql",
        )
        self.assertEqual(len(filtered), 1)
        criteria = (
            filtered[0]["cve"]["configurations"][0]["nodes"][0]
            ["cpeMatch"][0]["criteria"]
        )
        self.assertEqual(criteria, POSTGRES_CPE)

    def test_drops_non_matching_products(self) -> None:
        self.assertEqual(filter_cves([_vuln(MYSQL_CPE)], "postgresql"), [])

    def test_ignores_non_vulnerable_matches(self) -> None:
        self.assertEqual(
            filter_cves([_vuln(POSTGRES_CPE, vulnerable=False)], "postgresql"),
            [],
        )

    def test_ignores_malformed_entries(self) -> None:
        malformed = {
            "cve": {
                "configurations": [
                    {"nodes": [{"cpeMatch": [{"criteria": "not-cpe", "vulnerable": True}]}]}
                ]
            }
        }
        self.assertEqual(filter_cves([malformed], "postgresql"), [])

    def test_empty_input(self) -> None:
        self.assertEqual(filter_cves([], "postgresql"), [])