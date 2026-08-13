"""Tests for the NVD service with the network fully mocked."""

import unittest
from unittest import mock

import requests

from app.services import nvd_service

CPE = "cpe:2.3:a:postgresql:postgresql:16.4:*:*:*:*:*:*:*"
VULNS = [{"cve": {"id": "CVE-2024-0001"}}]


class GetCvesByCpeTests(unittest.TestCase):

    def setUp(self) -> None:
        nvd_service._CACHE.clear()

    def tearDown(self) -> None:
        nvd_service._CACHE.clear()

    def test_invalid_cpe_returns_empty(self) -> None:
        self.assertEqual(nvd_service.get_cves_by_cpe(None), [])
        self.assertEqual(nvd_service.get_cves_by_cpe("not-a-cpe"), [])

    def test_returns_fetched_vulnerabilities(self) -> None:
        with mock.patch.object(
            nvd_service,
            "_fetch_vulnerabilities_for_cpe",
            return_value=VULNS,
        ):
            result = nvd_service.get_cves_by_cpe(CPE)
        self.assertEqual(result, VULNS)

    def test_falls_back_to_keyword_search_on_http_error(self) -> None:
        with mock.patch.object(
            nvd_service,
            "_fetch_vulnerabilities_for_cpe",
            side_effect=requests.exceptions.HTTPError(),
        ):
            with mock.patch.object(
                nvd_service,
                "_fetch_vulnerabilities_by_keyword",
                return_value=VULNS,
            ) as keyword:
                result = nvd_service.get_cves_by_cpe(CPE)

        self.assertEqual(result, VULNS)
        keyword.assert_called_once()

    def test_caches_results_after_first_fetch(self) -> None:
        with mock.patch.object(
            nvd_service,
            "_fetch_vulnerabilities_for_cpe",
            return_value=VULNS,
        ) as fetch:
            first = nvd_service.get_cves_by_cpe(CPE)
            second = nvd_service.get_cves_by_cpe(CPE)

        self.assertEqual(first, VULNS)
        self.assertEqual(second, VULNS)
        fetch.assert_called_once()