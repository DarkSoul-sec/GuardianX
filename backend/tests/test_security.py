"""Tests for password hashing and verification."""

import unittest

from app.core.security import get_password_hash, verify_password

_PASSWORD = "GuardianX123!"


class PasswordHashTests(unittest.TestCase):

    def test_hash_round_trip(self) -> None:
        hashed = get_password_hash(_PASSWORD)
        self.assertTrue(verify_password(_PASSWORD, hashed))

    def test_verify_rejects_wrong_password(self) -> None:
        hashed = get_password_hash(_PASSWORD)
        self.assertFalse(verify_password("wrong-password", hashed))

    def test_hashes_are_salted(self) -> None:
        self.assertNotEqual(
            get_password_hash(_PASSWORD),
            get_password_hash(_PASSWORD),
        )