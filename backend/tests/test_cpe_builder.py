"""Tests for CPE 2.3 string construction."""

import unittest

from app.services.cpe_builder import build_cpe


class BuildCpeTests(unittest.TestCase):

    def test_postgresql_with_version(self) -> None:
        self.assertEqual(
            build_cpe("PostgreSQL DB", "16.4"),
            "cpe:2.3:a:postgresql:postgresql:16.4:*:*:*:*:*:*:*",
        )

    def test_apache_with_version(self) -> None:
        self.assertEqual(
            build_cpe("Apache httpd", "2.4.62"),
            "cpe:2.3:a:apache:apache:2.4.62:*:*:*:*:*:*:*",
        )

    def test_uvicorn_uses_encode_vendor(self) -> None:
        self.assertEqual(
            build_cpe("Uvicorn", "0.34.0"),
            "cpe:2.3:a:encode:uvicorn:0.34.0:*:*:*:*:*:*:*",
        )

    def test_missing_version_uses_wildcard(self) -> None:
        self.assertEqual(
            build_cpe("Redis", None),
            "cpe:2.3:a:redis:redis:*:*:*:*:*:*:*:*",
        )
        self.assertEqual(
            build_cpe("Redis", "  "),
            "cpe:2.3:a:redis:redis:*:*:*:*:*:*:*:*",
        )

    def test_unknown_product_passes_through_lowercased(self) -> None:
        cpe = build_cpe("CustomScript", "1.0")
        self.assertIsNotNone(cpe)
        self.assertIn("customscript", cpe)

    def test_missing_product_returns_none(self) -> None:
        self.assertIsNone(build_cpe(None, "1.0"))
        self.assertIsNone(build_cpe("", "1.0"))