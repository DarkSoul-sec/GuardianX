"""Outbound email delivery for account flows.

Delivers transactional mail (email verification, password reset, welcome) over
SMTP.

Delivery modes
--------------
* **SMTP delivery** — ``EMAIL_SMTP_HOST`` is configured: the message is sent
  over SMTP using STARTTLS (``EMAIL_USE_TLS=true``, port 587) or implicit SSL
  (``EMAIL_USE_SSL=true``, port 465). Only safe metadata is logged; tokens,
  passwords and full URLs are never written to the log.
* **Development / log only** — ``EMAIL_SMTP_HOST`` is empty: no real email is
  sent. The message payload is rendered to the log with an explicit
  ``EMAIL DELIVERY MODE: DEVELOPMENT / LOG ONLY`` marker so it is never
  mistaken for real delivery.

Outcomes are explicit:

* SMTP server accepted the message → ``DeliveryResult(delivered=True,
  mode="smtp", ...)``.
* No SMTP configured (log only) → ``DeliveryResult(delivered=False,
  mode="log_only", ...)``. This is **not** success: the message never reached a
  mailbox, so callers must not report it as sent.
* SMTP delivery failed → ``send_mail`` logs a targeted diagnostic and re-raises
  the underlying exception; no result is returned.

SMTP passwords, one-time tokens and full verification/reset URLs are never
written to the delivery logs.
"""

import re
import smtplib
import ssl
import uuid
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr

from app.core.config import settings
from app.logger import logger

DEV_MODE_LABEL = "EMAIL DELIVERY MODE: DEVELOPMENT / LOG ONLY"


@dataclass(frozen=True)
class DeliveryResult:
    """Outcome of a mail-delivery attempt.

    ``delivered`` is ``True`` only when a real SMTP server accepted the
    message. ``mode`` is ``"smtp"`` for a real delivery or ``"log_only"`` when
    no SMTP endpoint is configured and the payload was only rendered to the
    log. Delivery failures raise from :func:`send_mail` and never produce a
    result.
    """

    delivered: bool
    mode: str
    correlation_id: str


def _parse_from(value: str) -> str:
    """Interpret EMAIL_FROM as either ``addr@example.com`` or ``Name <addr@x>``.

    Returns a value safe for ``formataddr``.
    """
    value = value.strip()
    match = re.match(r"^(.*?)\s*<\s*([^<>]+@[^<>]+)\s*>$", value)

    if match:
        name, address = match.group(1).strip(), match.group(2).strip()
        return formataddr((name, address))

    # No display name: pass the plain address through untouched.
    return value


def _render(
    to_email: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = _parse_from(settings.EMAIL_FROM)
    message["To"] = to_email
    message.set_content(text_body)

    if html_body is not None:
        message.add_alternative(html_body, subtype="html")

    return message


def email_mode() -> str:
    """Human-readable label for how email delivery is configured."""
    if not settings.EMAIL_SMTP_HOST:
        return "DEVELOPMENT (LOG ONLY)"

    if settings.EMAIL_USE_SSL:
        return f"PRODUCTION (SMTP SSL, {settings.EMAIL_SMTP_HOST}:{settings.EMAIL_SMTP_PORT})"

    if settings.EMAIL_USE_TLS:
        return f"PRODUCTION (SMTP STARTTLS, {settings.EMAIL_SMTP_HOST}:{settings.EMAIL_SMTP_PORT})"

    return f"PRODUCTION (SMTP plaintext, {settings.EMAIL_SMTP_HOST}:{settings.EMAIL_SMTP_PORT})"


def validate_email_config(cfg: object = settings) -> bool:
    """Validate the email configuration and fail fast on misuse.

    Raises ``ValueError`` for contradictory/correct-by-construction settings and
    ``RuntimeError`` when production mode is configured without an SMTP
    endpoint so the failure is loud instead of silently log-only.
    """
    if cfg.EMAIL_USE_TLS and cfg.EMAIL_USE_SSL:
        raise ValueError(
            "EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be enabled. "
            "Pick STARTTLS on port 587 (EMAIL_USE_TLS=true) or implicit "
            "SSL on port 465 (EMAIL_USE_SSL=true)."
        )

    if not cfg.DEBUG and not cfg.EMAIL_SMTP_HOST:
        raise RuntimeError(
            "Production mode (DEBUG=false) requires EMAIL_SMTP_HOST. "
            "Emails are not being delivered — configure SMTP or run with "
            "DEBUG=true for development log-only delivery."
        )

    return True


def build_link(path: str) -> str:
    """Return an absolute URL to the frontend for a given route path.

    ``path`` should start with a leading slash, e.g. ``/reset-password``.
    """
    base = (settings.PUBLIC_APP_URL or "").strip().rstrip("/")

    if not base:
        raise ValueError(
            "PUBLIC_APP_URL is not configured; cannot build an email link."
        )

    return f"{base}{path}"


def _deliver(message: EmailMessage) -> None:
    """Open an SMTP connection, authenticate and transmit the message.

    The connection is always quitted (or closed) even when sending fails.
    Exceptions propagate to the caller for targeted handling/logging.
    """
    timeout = settings.EMAIL_SMTP_TIMEOUT_SECONDS

    client = smtplib.SMTP_SSL if settings.EMAIL_USE_SSL else smtplib.SMTP

    server = client(
        settings.EMAIL_SMTP_HOST,
        settings.EMAIL_SMTP_PORT,
        timeout=timeout,
    )

    try:
        if not settings.EMAIL_USE_SSL and settings.EMAIL_USE_TLS:
            server.starttls()

        if (
            settings.EMAIL_SMTP_USER
            and settings.EMAIL_SMTP_PASSWORD is not None
            and settings.EMAIL_SMTP_PASSWORD.get_secret_value()
        ):
            server.login(
                settings.EMAIL_SMTP_USER,
                settings.EMAIL_SMTP_PASSWORD.get_secret_value(),
            )

        server.send_message(message)
    finally:
        try:
            server.quit()
        except (smtplib.SMTPException, OSError, ssl.SSLError):
            server.close()


def send_mail(
    to_email: str,
    subject: str,
    body: str,
    html_body: str | None = None,
    *,
    email_type: str = "generic",
    correlation_id: str | None = None,
) -> DeliveryResult:
    """Deliver an email, or render it to the log in development mode.

    Returns a :class:`DeliveryResult`. ``delivered`` is ``True`` only when a
    real SMTP server accepted the message; log-only development mode reports
    ``delivered=False`` so callers never mistake it for a real send. SMTP
    delivery failures are **not** swallowed: they are logged and re-raised so
    the caller can react (e.g. roll back a pending signup).

    Only safe metadata is logged: correlation id, email type, recipient
    domain, attempt result and (when safe) the provider response code. SMTP
    passwords, one-time tokens and full verification/reset URLs are never
    written to the delivery logs.
    """
    correlation_id = correlation_id or uuid.uuid4().hex[:16]
    recipient_domain = to_email.rsplit("@", 1)[-1] if "@" in to_email else "unknown"

    # DEVELOPMENT / LOG ONLY: SMTP is not configured — the message never
    # reached a mailbox, so report delivered=False.
    if not settings.EMAIL_SMTP_HOST:
        logger.warning(
            "%s — no message was delivered to a mailbox. "
            "correlation_id=%s email_type=%s recipient_domain=%s",
            DEV_MODE_LABEL,
            correlation_id,
            email_type,
            recipient_domain,
        )
        logger.info(
            "Logged email payload (NOT delivered): to=%s subject=%r\n%s",
            to_email,
            subject,
            body,
        )
        return DeliveryResult(
            delivered=False,
            mode="log_only",
            correlation_id=correlation_id,
        )

    validate_email_config()

    message = _render(to_email, subject, body, html_body)

    logger.info(
        "Email delivery attempt: correlation_id=%s email_type=%s "
        "recipient_domain=%s host=%s port=%s mode=%s",
        correlation_id,
        email_type,
        recipient_domain,
        settings.EMAIL_SMTP_HOST,
        settings.EMAIL_SMTP_PORT,
        "SSL" if settings.EMAIL_USE_SSL
        else ("STARTTLS" if settings.EMAIL_USE_TLS else "plaintext"),
    )

    try:
        _deliver(message)
    except smtplib.SMTPAuthenticationError as exc:
        logger.error(
            "Email delivery failed (SMTP authentication error): "
            "correlation_id=%s email_type=%s recipient_domain=%s "
            "provider_code=%s",
            correlation_id,
            email_type,
            recipient_domain,
            exc.smtp_code,
        )
        raise
    except ssl.SSLError as exc:
        logger.error(
            "Email delivery failed (TLS/SSL error): correlation_id=%s "
            "email_type=%s recipient_domain=%s",
            correlation_id,
            email_type,
            recipient_domain,
        )
        raise
    except smtplib.SMTPException as exc:
        logger.error(
            "Email delivery failed (SMTP error): correlation_id=%s "
            "email_type=%s recipient_domain=%s provider_code=%s",
            correlation_id,
            email_type,
            recipient_domain,
            getattr(exc, "smtp_code", None),
        )
        raise
    except OSError as exc:
        logger.error(
            "Email delivery failed (connection error): correlation_id=%s "
            "email_type=%s recipient_domain=%s",
            correlation_id,
            email_type,
            recipient_domain,
        )
        raise

    logger.info(
        "Email delivery succeeded: correlation_id=%s email_type=%s "
        "recipient_domain=%s",
        correlation_id,
        email_type,
        recipient_domain,
    )

    return DeliveryResult(
        delivered=True,
        mode="smtp",
        correlation_id=correlation_id,
    )
