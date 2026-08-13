import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.email_token import EmailToken

KIND_VERIFY_EMAIL = "verify_email"
KIND_RESET_PASSWORD = "reset_password"


def generate_token() -> str:
    """Return a cryptographically secure one-time token."""
    return secrets.token_urlsafe(48)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_email_token(
    db: Session,
    user_id: int,
    kind: str,
    expires_minutes: int | None = None,
    *,
    commit: bool = True,
) -> str:
    """Create a one-time token, returning the plain-text value.

    Only the SHA-256 hash is stored, so a database leak does not expose live
    verification or password-reset tokens. ``commit=False`` defers the write
    so callers can group token creation into a larger transaction.
    """
    token = generate_token()

    expires_minutes = expires_minutes or (
        settings.EMAIL_VERIFICATION_EXPIRE_MINUTES
        if kind == KIND_VERIFY_EMAIL
        else settings.PASSWORD_RESET_EXPIRE_MINUTES
    )

    db_token = EmailToken(
        user_id=user_id,
        kind=kind,
        token_hash=_hash(token),
        expires_at=datetime.now(UTC) + timedelta(minutes=expires_minutes),
        used=False,
    )

    db.add(db_token)

    if commit:
        db.commit()
        db.refresh(db_token)
    else:
        db.flush()

    return token


def consume_email_token(
    db: Session,
    token: str,
    kind: str,
) -> EmailToken | None:
    """Validate and consume a one-time token.

    Returns the token row (marked used) on success, or ``None`` if the token
    is unknown, already used, expired, or of the wrong kind.
    """
    email_token = (
        db.query(EmailToken)
        .filter(
            EmailToken.token_hash == _hash(token),
            EmailToken.kind == kind,
            EmailToken.used.is_(False),
        )
        .first()
    )

    if email_token is None:
        return None

    expires_at = email_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if expires_at <= datetime.now(UTC):
        email_token.used = True
        db.commit()
        return None

    email_token.used = True
    db.commit()

    return email_token


def revoke_email_tokens(
    db: Session,
    user_id: int,
    kind: str,
) -> None:
    """Mark all outstanding tokens of a kind as used (single-use guarantee)."""
    tokens = (
        db.query(EmailToken)
        .filter(
            EmailToken.user_id == user_id,
            EmailToken.kind == kind,
            EmailToken.used.is_(False),
        )
        .all()
    )

    for token in tokens:
        token.used = True

    db.commit()