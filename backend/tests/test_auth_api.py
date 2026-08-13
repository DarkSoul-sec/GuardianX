"""End-to-end HTTP tests for the authentication flow using FastAPI TestClient."""

import re
import smtplib
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.roles import UserRole
from app.core.security import verify_password
from app.database.base import Base
from app.database import models  # noqa: F401 - register mapped models
from app.database.dependencies import get_db
from app.main import app as fastapi_app
from app.models.user import User
from app.services.mail_service import DeliveryResult

PASSWORD = "Sup3rStrongPassword1!"
NEW_PASSWORD = "BrandNewPassword123!"


class AuthFlowApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # In-memory SQLite with a single shared connection so the TestClient
        # worker thread and the main thread see identical data.
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(cls.engine)
        cls.SessionFactory = sessionmaker(bind=cls.engine)

    def setUp(self) -> None:
        self.db: Session = self.SessionFactory()

        def _override_get_db():
            try:
                yield self.db
            finally:
                pass

        fastapi_app.dependency_overrides[get_db] = _override_get_db
        self.client = TestClient(fastapi_app)

        # Default scenario: SMTP is configured and the transport is mocked, so
        # the mailer reports a real delivery. Tests that exercise the
        # unconfigured / failure paths override these. The signup / email
        # verification suite runs in "cloud" mode where that flow is enabled;
        # "local" mode behaviour is covered by the dedicated tests below.
        self._auth_mode_patch = patch.object(settings, "AUTH_MODE", "cloud")
        self._auth_mode_patch.start()
        self._smtp_host_patch = patch.object(
            settings, "EMAIL_SMTP_HOST", "smtp.example.com"
        )
        self._smtp_host_patch.start()
        self._deliver_patch = patch(
            "app.services.mail_service._deliver",
            return_value=None,
        )
        self._deliver_mock = self._deliver_patch.start()
        self.addCleanup(self._deliver_patch.stop)
        self.addCleanup(self._smtp_host_patch.stop)
        self.addCleanup(self._auth_mode_patch.stop)

    def tearDown(self) -> None:
        fastapi_app.dependency_overrides.clear()
        self.db.close()
        # Wipe data between tests (StaticPool keeps the in-memory DB alive).
        session = self.SessionFactory()
        try:
            for table in reversed(Base.metadata.sorted_tables):
                session.execute(table.delete())
            session.commit()
        finally:
            session.close()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def _signup(self, email="jane@example.com", username="jane"):
        return self.client.post(
            "/api/auth/signup",
            json={
                "username": username,
                "email": email,
                "password": PASSWORD,
            },
        )

    def _login(self, identifier="jane@example.com", password=PASSWORD):
        return self.client.post(
            "/api/auth/login",
            data={"username": identifier, "password": password},
        )

    def _verify_user(self, email="jane@example.com") -> None:
        """Complete a real verification through the API, as a link click would."""
        from app.services.email_token_service import KIND_VERIFY_EMAIL, create_email_token

        user = self.db.query(User).filter(User.email == email).one()
        token = create_email_token(self.db, user.id, KIND_VERIFY_EMAIL)
        response = self.client.post("/api/auth/verify-email", json={"token": token})
        self.assertEqual(response.status_code, 200)

    def test_signup_returns_user_unverified(self) -> None:
        response = self._signup()

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["username"], "jane")
        self.assertFalse(body["email_verified"])
        # The account must start in a pending, inactive state.
        self.assertFalse(body["is_active"])

    def test_signup_rejects_duplicate_email(self) -> None:
        self._signup()

        response = self.client.post(
            "/api/auth/signup",
            json={"username": "jane2", "email": "jane@example.com", "password": PASSWORD},
        )
        self.assertEqual(response.status_code, 400)

    def test_login_success_returns_token_pair(self) -> None:
        self._signup()
        self._verify_user()

        response = self._login()
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("access_token", body)
        self.assertIn("refresh_token", body)

    def test_login_before_verification_is_blocked(self) -> None:
        self._signup()

        # Unverified accounts must not be able to sign in.
        self.assertEqual(self._login().status_code, 401)

    def test_login_with_username_or_email(self) -> None:
        self._signup()
        self._verify_user()

        by_email = self._login("jane@example.com", PASSWORD)
        by_username = self._login("jane", PASSWORD)
        self.assertEqual(by_email.status_code, 200)
        self.assertEqual(by_username.status_code, 200)

    def test_login_wrong_password(self) -> None:
        self._signup()
        self._verify_user()
        self.assertEqual(self._login(password="WrongPassword123!").status_code, 401)

    def test_forgot_password_is_enumeration_safe(self) -> None:
        self._signup()

        for payload in [{"email": "nobody@example.com"}, {"email": "jane@example.com"}]:
            response = self.client.post("/api/auth/forgot-password", json=payload)
            self.assertEqual(response.status_code, 200)
            self.assertIn(
                "If that email is registered",
                response.json()["message"],
            )

    def test_signup_email_delivery_failure_returns_error_and_rolls_back(self) -> None:
        # SMTP configured but the transport rejects the message: signup must
        # NOT report success and must not leave an account behind.
        with patch(
            "app.services.mail_service._deliver",
            side_effect=smtplib.SMTPException((550, b"rejected")),
        ):
            response = self._signup()
            self.assertEqual(response.status_code, 502)
            self.assertIn(
                "could not send your verification email",
                response.json()["detail"].lower(),
            )

        # Nothing was committed: the account cannot be found and login fails.
        self.assertIsNone(self.db.query(User).filter_by(email="jane@example.com").first())
        self.assertEqual(self._login().status_code, 401)
        # A clean retry succeeds once the mailer is healthy again.
        self.assertEqual(self._signup().status_code, 201)

    def test_signup_email_service_not_configured_returns_503(self) -> None:
        # SMTP missing (development/log-only mode): signup must NOT report the
        # email as sent, so the frontend must not show "Almost There".
        with patch.object(settings, "EMAIL_SMTP_HOST", ""):
            response = self._signup()
            self.assertEqual(response.status_code, 503)
            self.assertIn(
                "verification email service is not configured",
                response.json()["detail"].lower(),
            )

        # No transport was ever contacted.
        self._deliver_mock.assert_not_called()
        # Account was rolled back and stays pending/non-existent.
        self.assertIsNone(self.db.query(User).filter_by(email="jane@example.com").first())
        self.assertEqual(self._login().status_code, 401)

    def test_signup_smtp_success_reports_delivery(self) -> None:
        # SMTP configured + accepted: signup succeeds (the frontend is then
        # entitled to show "Almost There").
        self._deliver_mock.assert_not_called()
        response = self._signup()
        self.assertEqual(response.status_code, 201)
        self._deliver_mock.assert_called()

        user = self.db.query(User).filter_by(email="jane@example.com").one()
        self.assertFalse(user.email_verified)
        self.assertFalse(user.is_active)

    def test_verify_email_activates_account(self) -> None:
        self._signup()
        self._verify_user()

        user = self.db.query(User).filter_by(email="jane@example.com").one()
        self.assertTrue(user.email_verified)
        self.assertTrue(user.is_active)

    def test_full_reset_password_flow(self) -> None:
        self._signup()
        self._verify_user()

        captured: list[str] = []

        def fake_send(
            to_email, subject, body, html_body=None, *, email_type=None, correlation_id=None
        ):
            captured.append(body)

        with patch("app.api.v1.auth.send_mail", side_effect=fake_send):
            response = self.client.post(
                "/api/auth/forgot-password",
                json={"email": "jane@example.com"},
            )
            self.assertEqual(response.status_code, 200)

        self.assertEqual(len(captured), 1)
        match = re.search(r"token=([^\s]+)", captured[0])
        self.assertIsNotNone(match)
        token = match.group(1)

        # New password is rejected with bad token.
        bad = self.client.post(
            "/api/auth/reset-password",
            json={"token": "bogus-token", "new_password": NEW_PASSWORD},
        )
        self.assertEqual(bad.status_code, 400)

        ok = self.client.post(
            "/api/auth/reset-password",
            json={"token": token, "new_password": NEW_PASSWORD},
        )
        self.assertEqual(ok.status_code, 200)

        # Old password no longer works.
        self.assertEqual(self._login(password=PASSWORD).status_code, 401)
        # New password works.
        self.assertEqual(self._login(password=NEW_PASSWORD).status_code, 200)
        # Token is single-use: a second attempt fails.
        reuse = self.client.post(
            "/api/auth/reset-password",
            json={"token": token, "new_password": NEW_PASSWORD},
        )
        self.assertEqual(reuse.status_code, 400)

    def test_verify_email_flow(self) -> None:
        self._signup()

        from app.services.email_token_service import KIND_VERIFY_EMAIL, create_email_token

        token = create_email_token(self.db, 1, KIND_VERIFY_EMAIL)

        bad = self.client.post("/api/auth/verify-email", json={"token": "nope"})
        self.assertEqual(bad.status_code, 400)

        ok = self.client.post("/api/auth/verify-email", json={"token": token})
        self.assertEqual(ok.status_code, 200)

        user = self.db.query(User).first()
        self.assertTrue(user.email_verified)
        # Verification is what activates the account.
        self.assertTrue(user.is_active)

        # Token is single-use.
        again = self.client.post("/api/auth/verify-email", json={"token": token})
        self.assertEqual(again.status_code, 400)

    def test_resend_verification_invalidates_previous_token(self) -> None:
        captured: list[str] = []

        def fake_send(
            to_email, subject, body, html_body=None, *, email_type=None, correlation_id=None
        ):
            if email_type == "verification":
                captured.append(body)
            return DeliveryResult(
                delivered=True,
                mode="smtp",
                correlation_id=correlation_id or "test",
            )

        with patch("app.api.v1.auth.send_mail", side_effect=fake_send):
            # Signup verification email (captured[0]).
            self._signup()
            # Resend verification email (captured[1]).
            response = self.client.post(
                "/api/auth/resend-verification",
                json={"email": "jane@example.com"},
            )
            self.assertEqual(response.status_code, 200)

        self.assertEqual(len(captured), 2)
        old_token = re.search(r"token=([^\s]+)", captured[0]).group(1)
        new_token = re.search(r"token=([^\s]+)", captured[1]).group(1)
        self.assertNotEqual(old_token, new_token)

        # New token works and activates the account.
        ok = self.client.post("/api/auth/verify-email", json={"token": new_token})
        self.assertEqual(ok.status_code, 200)

        # Old token was revoked by the resend and is rejected.
        stale = self.client.post("/api/auth/verify-email", json={"token": old_token})
        self.assertEqual(stale.status_code, 400)

    def test_resend_verification_reports_delivery_failure(self) -> None:
        self._signup()

        with patch(
            "app.services.mail_service._deliver",
            side_effect=smtplib.SMTPException((550, b"rejected")),
        ):
            response = self.client.post(
                "/api/auth/resend-verification",
                json={"email": "jane@example.com"},
            )
            self.assertEqual(response.status_code, 502)

    def test_resend_verification_service_not_configured_returns_503(self) -> None:
        self._signup()

        with patch.object(settings, "EMAIL_SMTP_HOST", ""):
            response = self.client.post(
                "/api/auth/resend-verification",
                json={"email": "jane@example.com"},
            )
            self.assertEqual(response.status_code, 503)

        user = self.db.query(User).filter_by(email="jane@example.com").one()
        # Account stays unverified and inactive.
        self.assertFalse(user.email_verified)
        self.assertFalse(user.is_active)

    # ---- Local mode: first-run setup and local authentication ----

    def _local_mode(self):
        return patch.object(settings, "AUTH_MODE", "local")

    def _setup(self, username="admin", password=PASSWORD):
        return self.client.post(
            "/api/auth/setup",
            json={"username": username, "password": password},
        )

    def _local_login(self, username="admin", password=PASSWORD):
        return self.client.post(
            "/api/auth/login",
            data={"username": username, "password": password},
        )

    def test_setup_status_reports_uninitialized(self) -> None:
        with self._local_mode():
            response = self.client.get("/api/auth/setup-status")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertFalse(body["initialized"])
        self.assertEqual(body["auth_mode"], "local")

    def test_setup_creates_initial_administrator(self) -> None:
        with self._local_mode():
            response = self._setup()

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "initialized successfully",
            response.json()["message"],
        )

        admin = self.db.query(User).filter_by(username="admin").one()
        self.assertEqual(admin.role, UserRole.ADMIN)
        self.assertTrue(admin.is_active)
        self.assertIsNone(admin.email)
        self.assertNotEqual(admin.password_hash, PASSWORD)

    def test_setup_password_is_hashed_never_plaintext(self) -> None:
        with self._local_mode():
            self._setup()

        admin = self.db.query(User).filter_by(username="admin").one()
        self.assertNotIn(PASSWORD, admin.password_hash)
        self.assertTrue(verify_password(PASSWORD, admin.password_hash))

    def test_setup_status_reports_initialized_after_setup(self) -> None:
        with self._local_mode():
            self._setup()
            response = self.client.get("/api/auth/setup-status")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["initialized"])

    def test_setup_is_permanently_unavailable_after_initialization(self) -> None:
        with self._local_mode():
            self._setup()
            first = self._setup()
            second = self._setup(username="intruder", password=NEW_PASSWORD)
            status = self.client.get("/api/auth/setup-status")

        self.assertEqual(first.status_code, 409)
        self.assertEqual(second.status_code, 409)
        self.assertTrue(status.json()["initialized"])
        # No second administrator was ever created.
        self.assertIsNone(
            self.db.query(User).filter_by(username="intruder").first()
        )
        admins = self.db.query(User).filter(User.role == UserRole.ADMIN).all()
        self.assertEqual(len(admins), 1)

    def test_setup_rejects_taken_username(self) -> None:
        # A non-admin account may already exist (e.g. an upgraded install).
        # Setup with that username must be rejected without creating an admin.
        self._signup()
        self._verify_user()

        with self._local_mode():
            response = self._setup(username="jane")
            status = self.client.get("/api/auth/setup-status")

        self.assertEqual(response.status_code, 400)
        self.assertFalse(status.json()["initialized"])
        self.assertIsNone(
            self.db.query(User).filter(User.role == UserRole.ADMIN).first()
        )

    def test_signup_is_disabled_in_local_mode(self) -> None:
        with self._local_mode():
            response = self._signup()

        self.assertEqual(response.status_code, 403)
        self.assertIsNone(
            self.db.query(User).filter_by(email="jane@example.com").first()
        )

    def test_local_administrator_logs_in_without_email_verification(self) -> None:
        with self._local_mode():
            self._setup()
            login = self._local_login()

        self.assertEqual(login.status_code, 200)
        self.assertIn("access_token", login.json())
        self.assertIn("refresh_token", login.json())

    def test_local_administrator_wrong_password_rejected(self) -> None:
        with self._local_mode():
            self._setup()
            login = self._local_login(password="WrongPassword123!")

        self.assertEqual(login.status_code, 401)

    def test_refresh_works_for_local_administrator(self) -> None:
        with self._local_mode():
            self._setup()
            login = self._local_login()
            refresh = self.client.post(
                "/api/auth/refresh",
                json={"refresh_token": login.json()["refresh_token"]},
            )

        self.assertEqual(refresh.status_code, 200)
        self.assertIn("access_token", refresh.json())

    def test_unauthenticated_dashboard_denied(self) -> None:
        with self._local_mode():
            response = self.client.get("/api/dashboard")

        self.assertEqual(response.status_code, 401)

    def test_authenticated_dashboard_allowed(self) -> None:
        with self._local_mode():
            self._setup()
            login = self._local_login()
            token = login.json()["access_token"]
            response = self.client.get(
                "/api/dashboard",
                headers={"Authorization": f"Bearer {token}"},
            )

        self.assertEqual(response.status_code, 200)

    def test_me_requires_auth(self) -> None:
        self.assertEqual(self.client.get("/api/users/me").status_code, 401)

    def test_me_sessions_list(self) -> None:
        self._signup()
        self._verify_user()
        login = self._login()
        token = login.json()["access_token"]

        response = self.client.get(
            "/api/users/me/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        sessions = response.json()["sessions"]
        self.assertEqual(len(sessions), 1)


class InvalidJwtApiTests(AuthFlowApiTests):
    """
    Regression: invalid authentication credentials must produce 401, never 500.

    Every JWT failure mode (garbage, malformed, expired, bad signature) and a
    missing token must be rejected as 401 with a Bearer challenge. A valid
    access token must still authenticate normally, and a revoked refresh token
    must still be rejected at the refresh endpoint.
    """

    def _local_admin(self) -> User:
        with self._local_mode():
            self._setup()
        return self.db.query(User).filter_by(username="admin").one()

    def _valid_token(self) -> str:
        with self._local_mode():
            self._setup()
            return self._local_login().json()["access_token"]

    def _get(self, token: str | None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        return self.client.get("/api/users/me", headers=headers)

    def _assert_401(self, response) -> None:
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["code"], "unauthorized")
        self.assertIn("Bearer", response.headers.get("www-authenticate", ""))

    def test_valid_access_token_grants_access(self) -> None:
        with self._local_mode():
            self._setup()
            login = self._local_login()
            response = self.client.get(
                "/api/users/me",
                headers={"Authorization": f"Bearer {login.json()['access_token']}"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "admin")

    def test_garbage_token_returns_401(self) -> None:
        self._assert_401(self._get("not-a-jwt-at-all"))

    def test_malformed_token_returns_401(self) -> None:
        # Well-formed prefix but missing the signature segment.
        truncated = self._valid_token().rsplit(".", 1)[0]
        self._assert_401(self._get(truncated))

    def test_expired_token_returns_401(self) -> None:
        admin = self._local_admin()
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(admin.id),
            "username": admin.username,
            "type": "access",
            "iss": settings.APP_NAME,
            "aud": "guardianx-api",
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
        }
        expired = jwt.encode(
            payload,
            settings.SECRET_KEY.get_secret_value(),
            algorithm=settings.ALGORITHM,
        )
        self._assert_401(self._get(expired))

    def test_invalid_signature_token_returns_401(self) -> None:
        admin = self._local_admin()
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(admin.id),
            "username": admin.username,
            "type": "access",
            "iss": settings.APP_NAME,
            "aud": "guardianx-api",
            "iat": now,
            "exp": now + timedelta(hours=1),
        }
        forged = jwt.encode(
            payload,
            "attacker-controlled-secret-key-000000000000000000000000",
            algorithm=settings.ALGORITHM,
        )
        self._assert_401(self._get(forged))

    def test_missing_token_returns_401(self) -> None:
        self._assert_401(self._get(None))

    def test_revoked_refresh_token_returns_401(self) -> None:
        with self._local_mode():
            self._setup()
            login = self._local_login()
            refresh = login.json()["refresh_token"]

            logout = self.client.post(
                "/api/auth/logout",
                json={"refresh_token": refresh},
            )
            reuse = self.client.post(
                "/api/auth/refresh",
                json={"refresh_token": refresh},
            )

        self.assertEqual(logout.status_code, 204)
        self.assertEqual(reuse.status_code, 401)


if __name__ == "__main__":
    unittest.main()