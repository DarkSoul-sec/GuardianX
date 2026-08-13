"""Regression tests for credential and account-status authentication checks."""

import unittest
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.auth import create_access_token
from app.core.config import settings
from app.database.base import Base
from app.database import models  # noqa: F401 - register mapped models
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.auth_service import authenticate_user, create_user


class AuthenticationFlowTests(unittest.TestCase):
    """Verify the authentication outcomes that must remain stable."""

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
                username="testuser",
                email="test@example.com",
                password="GuardianX123!",
            ),
        )

    def _verify_user(self) -> None:
        """Activate + verify the freshly created user (as /auth/verify-email
        would after a real link click)."""
        self.user.is_active = True
        self.user.email_verified = True
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def test_valid_credentials_authenticate_the_verified_user(self) -> None:
        self._verify_user()

        user = authenticate_user(
            self.db,
            "test@example.com",
            "GuardianX123!",
        )

        self.assertEqual(user.id, self.user.id)

    def test_pending_inactive_user_cannot_authenticate(self) -> None:
        # Account created pending (is_active=False, email_verified=False) must
        # not be able to log in: the inactive status blocks it regardless of
        # the auth mode.
        self.assertFalse(self.user.is_active)
        self.assertFalse(self.user.email_verified)
        self.assertIsNone(
            authenticate_user(self.db, "test@example.com", "GuardianX123!")
        )

    def test_local_mode_allows_active_unverified_user(self) -> None:
        # In the local edition, email verification is not a login gate: an
        # active account with a NULL/unverified email authenticates fine.
        self.user.is_active = True
        self.db.commit()

        user = authenticate_user(
            self.db,
            "test@example.com",
            "GuardianX123!",
        )
        self.assertEqual(user.id, self.user.id)

    def test_cloud_mode_blocks_active_unverified_user(self) -> None:
        # Cloud mode keeps the strict verified-email requirement.
        self.user.is_active = True
        self.db.commit()

        with patch.object(settings, "AUTH_MODE", "cloud"):
            self.assertIsNone(
                authenticate_user(
                    self.db,
                    "test@example.com",
                    "GuardianX123!",
                )
            )

    def test_username_can_be_used_when_it_differs_from_email(self) -> None:
        self._verify_user()

        user = authenticate_user(
            self.db,
            "testuser",
            "GuardianX123!",
        )

        self.assertEqual(user.id, self.user.id)
        user = authenticate_user(
            self.db,
            "testuser",
            "GuardianX123!",
        )

        self.assertEqual(user.id, self.user.id)

    def test_invalid_password_is_rejected(self) -> None:
        self._verify_user()

        self.assertIsNone(
            authenticate_user(self.db, "test@example.com", "incorrect-password")
        )

    def test_inactive_user_cannot_authenticate_or_use_existing_token(self) -> None:
        self._verify_user()
        self.user.is_active = False
        self.db.commit()

        self.assertIsNone(
            authenticate_user(self.db, "test@example.com", "GuardianX123!")
        )

        token = create_access_token({"sub": str(self.user.id)})
        with self.assertRaisesRegex(Exception, "User account is inactive"):
            get_current_user(token=token, db=self.db)

    def test_unsupported_password_hash_is_rejected(self) -> None:
        self._verify_user()
        self.user.password_hash = "not-a-password-hash"
        self.db.commit()

        self.assertIsNone(
            authenticate_user(self.db, "test@example.com", "GuardianX123!")
        )

    def test_malformed_subject_claim_is_rejected_as_unauthorized(self) -> None:
        token = create_access_token({"sub": "not-a-user-id"})

        with self.assertRaises(HTTPException) as error:
            get_current_user(token=token, db=self.db)

        self.assertEqual(error.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
