"""Tests for email verification and password-reset token flows."""

import re
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.database.base import Base
from app.database import models  # noqa: F401 - register mapped models
from app.models.email_token import EmailToken
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.auth_service import create_user
from app.services.email_token_service import (
    KIND_RESET_PASSWORD,
    KIND_VERIFY_EMAIL,
    consume_email_token,
    create_email_token,
    revoke_email_tokens,
)
from app.services.mail_service import _render, build_link


def _extract_token(log_line: str) -> str | None:
    """Pull the one-time token out of a logged email body link."""
    return match.group(1) if (match := re.search(r"token=([^\s]+)", log_line)) else None


class EmailTokenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)
        cls.session_factory = sessionmaker(bind=cls.engine)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def setUp(self) -> None:
        self.db: Session = self.session_factory()
        self.user = create_user(
            self.db,
            UserCreate(
                username="flowuser",
                email="flow@example.com",
                password="GuardianX123!",
            ),
        )

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def test_stored_token_is_only_a_hash(self) -> None:
        plain = create_email_token(self.db, self.user.id, KIND_VERIFY_EMAIL)

        row = self.db.query(EmailToken).filter_by(user_id=self.user.id).one()
        self.assertNotEqual(row.token_hash, plain)
        self.assertFalse(row.used)

    def test_valid_token_can_be_consumed_once(self) -> None:
        plain = create_email_token(self.db, self.user.id, KIND_VERIFY_EMAIL)

        first = consume_email_token(self.db, plain, KIND_VERIFY_EMAIL)
        self.assertIsNotNone(first)

        # Same token cannot be reused.
        second = consume_email_token(self.db, plain, KIND_VERIFY_EMAIL)
        self.assertIsNone(second)

    def test_unknown_or_wrong_kind_token_is_rejected(self) -> None:
        plain = create_email_token(self.db, self.user.id, KIND_VERIFY_EMAIL)

        self.assertIsNone(consume_email_token(self.db, "not-a-real-token", KIND_VERIFY_EMAIL))
        self.assertIsNone(consume_email_token(self.db, plain, KIND_RESET_PASSWORD))

    def test_expired_token_is_rejected(self) -> None:
        plain = create_email_token(
            self.db,
            self.user.id,
            KIND_VERIFY_EMAIL,
            expires_minutes=-1,
        )

        self.assertIsNone(consume_email_token(self.db, plain, KIND_VERIFY_EMAIL))

    def test_revoke_marks_all_outstanding_tokens_used(self) -> None:
        create_email_token(self.db, self.user.id, KIND_RESET_PASSWORD)
        create_email_token(self.db, self.user.id, KIND_RESET_PASSWORD)

        revoke_email_tokens(self.db, self.user.id, KIND_RESET_PASSWORD)

        remaining = self.db.query(EmailToken).filter_by(
            user_id=self.user.id,
        ).all()
        self.assertTrue(all(t.used for t in remaining))

    def test_build_link_normalizes_public_url(self) -> None:
        with patch.object(settings, "PUBLIC_APP_URL", "https://app.example.com/"):
            self.assertEqual(
                build_link("/reset-password"),
                "https://app.example.com/reset-password",
            )

    def test_render_accepts_email_from_as_name_and_address(self) -> None:
        cases = [
            ("GuardianX <noreply@localhost>", "GuardianX"),
            ("Noreply <no-reply@example.com>", "Noreply"),
            ("noreply@example.com", "noreply@example.com"),
        ]
        for email_from, expected in cases:
            with self.subTest(email_from=email_from):
                with patch.object(settings, "EMAIL_FROM", email_from):
                    message = _render("to@example.com", "Subject", "body")
                    self.assertEqual(message["To"], "to@example.com")
                    self.assertIn(expected, message["From"])


if __name__ == "__main__":
    unittest.main()