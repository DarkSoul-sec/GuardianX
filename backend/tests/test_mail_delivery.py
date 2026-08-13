"""Tests for outbound email delivery: the no-SMTP fallback, credential
handling, STARTTLS vs SSL, connection management, timeout and safe logging."""

import logging
import smtplib
import unittest
from unittest.mock import patch

from pydantic import SecretStr

from app.core.config import settings
from app.services.mail_service import DEV_MODE_LABEL, build_link, send_mail


class SendMailTests(unittest.TestCase):

    def test_no_smtp_host_reports_log_only_not_delivered(self) -> None:
        with patch.object(settings, "EMAIL_SMTP_HOST", ""):
            with patch("smtplib.SMTP") as smtp:
                result = send_mail("to@example.com", "Subject", "body")

        smtp.assert_not_called()
        # Log-only mode must never be reported as a real delivery.
        self.assertFalse(result.delivered)
        self.assertEqual(result.mode, "log_only")

    def test_sends_without_login_when_no_credentials(self) -> None:
        with patch.object(settings, "EMAIL_SMTP_HOST", "smtp.example.com"):
            with patch.object(settings, "EMAIL_USE_TLS", True):
                with patch.object(settings, "EMAIL_USE_SSL", False):
                    with patch.object(settings, "EMAIL_SMTP_USER", ""):
                        with patch.object(settings, "EMAIL_SMTP_PASSWORD", None):
                            with patch("smtplib.SMTP") as smtp:
                                server = smtp.return_value
                                result = send_mail("to@example.com", "Subject", "body")

        smtp.assert_called_once()
        server.login.assert_not_called()
        server.send_message.assert_called_once()
        server.quit.assert_called_once()
        self.assertTrue(result.delivered)
        self.assertEqual(result.mode, "smtp")

    def test_sends_with_login_when_credentials_configured(self) -> None:
        with patch.object(settings, "EMAIL_SMTP_HOST", "smtp.example.com"):
            with patch.object(settings, "EMAIL_USE_TLS", True):
                with patch.object(settings, "EMAIL_USE_SSL", False):
                    with patch.object(settings, "EMAIL_SMTP_USER", "apikey"):
                        with patch.object(settings, "EMAIL_SMTP_PASSWORD", SecretStr("secret")):
                            with patch("smtplib.SMTP") as smtp:
                                server = smtp.return_value
                                result = send_mail("to@example.com", "Subject", "body")

        server.login.assert_called_once_with("apikey", "secret")
        server.send_message.assert_called_once()
        self.assertTrue(result.delivered)
        self.assertEqual(result.mode, "smtp")

    def test_does_not_crash_when_user_set_but_password_missing(self) -> None:
        with patch.object(settings, "EMAIL_SMTP_HOST", "smtp.example.com"):
            with patch.object(settings, "EMAIL_USE_TLS", True):
                with patch.object(settings, "EMAIL_USE_SSL", False):
                    with patch.object(settings, "EMAIL_SMTP_USER", "apikey"):
                        with patch.object(settings, "EMAIL_SMTP_PASSWORD", None):
                            with patch("smtplib.SMTP") as smtp:
                                server = smtp.return_value
                                send_mail("to@example.com", "Subject", "body")

        server.login.assert_not_called()
        server.send_message.assert_called_once()

    def test_does_not_crash_when_password_is_empty(self) -> None:
        with patch.object(settings, "EMAIL_SMTP_HOST", "smtp.example.com"):
            with patch.object(settings, "EMAIL_USE_TLS", True):
                with patch.object(settings, "EMAIL_USE_SSL", False):
                    with patch.object(settings, "EMAIL_SMTP_USER", "apikey"):
                        with patch.object(settings, "EMAIL_SMTP_PASSWORD", SecretStr("")):
                            with patch("smtplib.SMTP") as smtp:
                                server = smtp.return_value
                                send_mail("to@example.com", "Subject", "body")

        server.login.assert_not_called()
        server.send_message.assert_called_once()

    def test_starttls_used_when_use_tls(self) -> None:
        with patch.object(settings, "EMAIL_SMTP_HOST", "smtp.example.com"):
            with patch.object(settings, "EMAIL_USE_TLS", True):
                with patch.object(settings, "EMAIL_USE_SSL", False):
                    with patch("smtplib.SMTP") as smtp:
                        server = smtp.return_value
                        send_mail("to@example.com", "Subject", "body")

        server.starttls.assert_called_once()

    def test_implicit_ssl_uses_smtp_ssl(self) -> None:
        with patch.object(settings, "EMAIL_SMTP_HOST", "smtp.example.com"):
            with patch.object(settings, "EMAIL_USE_TLS", False):
                with patch.object(settings, "EMAIL_USE_SSL", True):
                    with patch("smtplib.SMTP_SSL") as smtp_ssl:
                        server = smtp_ssl.return_value
                        send_mail("to@example.com", "Subject", "body")

        smtp_ssl.assert_called_once()
        server.starttls.assert_not_called()
        server.send_message.assert_called_once()

    def test_connection_close_falls_back_on_send_failure(self) -> None:
        with patch.object(settings, "EMAIL_SMTP_HOST", "smtp.example.com"):
            with patch.object(settings, "EMAIL_USE_TLS", True):
                with patch.object(settings, "EMAIL_USE_SSL", False):
                    with patch("smtplib.SMTP") as smtp:
                        server = smtp.return_value
                        server.send_message.side_effect = smtplib.SMTPException(
                            (550, b"rejected")
                        )
                        server.quit.side_effect = OSError("connection reset")
                        with self.assertRaises(smtplib.SMTPException):
                            send_mail("to@example.com", "Subject", "body")

        server.quit.assert_called()
        server.close.assert_called()

    def test_auth_failure_re_raises(self) -> None:
        from smtplib import SMTPAuthenticationError

        with patch.object(settings, "EMAIL_SMTP_HOST", "smtp.example.com"):
            with patch.object(settings, "EMAIL_USE_TLS", True):
                with patch.object(settings, "EMAIL_USE_SSL", False):
                    with patch.object(settings, "EMAIL_SMTP_USER", "user"):
                        with patch.object(settings, "EMAIL_SMTP_PASSWORD", SecretStr("pass")):
                            with patch("smtplib.SMTP") as smtp:
                                server = smtp.return_value
                                server.login.side_effect = SMTPAuthenticationError(535, b"denied")
                                with self.assertRaises(SMTPAuthenticationError):
                                    send_mail("to@example.com", "Subject", "body")

    def test_timeout_passed_to_smtp_constructor(self) -> None:
        with patch.object(settings, "EMAIL_SMTP_HOST", "smtp.example.com"):
            with patch.object(settings, "EMAIL_SMTP_PORT", 587):
                with patch.object(settings, "EMAIL_USE_TLS", True):
                    with patch.object(settings, "EMAIL_USE_SSL", False):
                        with patch.object(settings, "EMAIL_SMTP_TIMEOUT_SECONDS", 7):
                            with patch("smtplib.SMTP") as smtp:
                                send_mail("to@example.com", "Subject", "body")

        smtp.assert_called_once_with("smtp.example.com", 587, timeout=7)


class SafeLoggingTests(unittest.TestCase):
    """Fields; never the sensitive URL/token or the SMTP password."""

    def test_production_logs_safe_metadata_only(self) -> None:
        with patch.object(settings, "EMAIL_SMTP_HOST", "smtp.example.com"):
            with patch.object(settings, "EMAIL_USE_TLS", True):
                with patch.object(settings, "EMAIL_USE_SSL", False):
                    with patch("smtplib.SMTP") as smtp:
                        server = smtp.return_value
                        server.send_message.return_value = None
                        with self.assertLogs(logging.getLogger("guardianx"), level="INFO") as cm:
                            send_mail(
                                "secret@corp.example",
                                "Reset your password",
                                "hi https://localhost/reset?token=abc123abc",
                                email_type="password_reset",
                                correlation_id="corr123",
                            )

        text = "\n".join(cm.output)
        self.assertIn("password_reset", text)
        self.assertIn("corr123", text)
        self.assertIn("corp.example", text)
        self.assertNotIn("abc123abc", text)
        self.assertNotIn("https://localhost", text)


class DevModeTests(unittest.TestCase):

    def test_dev_mode_log_labels_specifically_and_never_claims_delivery(self) -> None:
        with patch.object(settings, "EMAIL_SMTP_HOST", ""):
            with patch("smtplib.SMTP") as smtp:
                with self.assertLogs(logging.getLogger("guardianx"), level="INFO") as cm:
                    result = send_mail(
                        "to@example.com",
                        "Verify your account",
                        "https://localhost/verify-email?token=devtoken",
                    )

        smtp.assert_not_called()
        text = "\n".join(cm.output)
        self.assertIn(DEV_MODE_LABEL, text)
        self.assertIn("devtoken", text)
        # Log-only mode must not be reported as delivered.
        self.assertFalse(result.delivered)
        self.assertEqual(result.mode, "log_only")


class BuildLinkTests(unittest.TestCase):

    def test_build_link_uses_public_app_url(self) -> None:
        with patch.object(settings, "PUBLIC_APP_URL", "https://app.example.com"):
            self.assertEqual(
                build_link("/reset-password?token=abc"),
                "https://app.example.com/reset-password?token=abc",
            )

    def test_build_link_raises_without_public_url(self) -> None:
        with patch.object(settings, "PUBLIC_APP_URL", ""):
            with self.assertRaises(ValueError):
                build_link("/verify-email")


if __name__ == "__main__":
    unittest.main()