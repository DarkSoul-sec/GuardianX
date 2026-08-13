"""Tests for product name normalization."""

import unittest

from app.services.product_normalizer import normalize_product


class NormalizeProductTests(unittest.TestCase):

    def test_postgresql_variants(self) -> None:
        for name in ("PostgreSQL DB", "PostgreSQL", "postgres"):
            self.assertEqual(normalize_product(name), "postgresql")

    def test_apache_variants(self) -> None:
        for name in ("Apache httpd", "Apache HTTP Server", "Apache"):
            self.assertEqual(normalize_product(name), "apache")

    def test_uvicorn(self) -> None:
        self.assertEqual(normalize_product("Uvicorn"), "uvicorn")

    def test_unknown_product_passes_through_lowercased(self) -> None:
        self.assertEqual(normalize_product("Node.js"), "node.js")
        self.assertEqual(normalize_product("  Nginx  "), "nginx")

    def test_missing_product_returns_none(self) -> None:
        self.assertIsNone(normalize_product(None))
        self.assertIsNone(normalize_product(""))