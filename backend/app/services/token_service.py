import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.refresh_token import RefreshToken


def generate_refresh_token() -> str:
    """
    Generate a cryptographically secure refresh token.
    """
    return secrets.token_urlsafe(64)


def hash_refresh_token(token: str) -> str:
    """
    Return the SHA-256 hash of a refresh token.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def store_refresh_token(
    db: Session,
    user_id: int,
    refresh_token: str,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> RefreshToken:
    """
    Store only the hashed refresh token.
    """

    db_token = RefreshToken(
        user_id=user_id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        revoked=False,
        user_agent=user_agent,
        ip_address=ip_address,
    )

    db.add(db_token)
    db.commit()
    db.refresh(db_token)

    return db_token


def get_refresh_token(
    db: Session,
    refresh_token: str,
) -> RefreshToken | None:
    """
    Find a refresh token by its SHA-256 hash.
    """

    token_hash = hash_refresh_token(refresh_token)

    return (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked.is_(False),
        )
        .first()
    )


def revoke_refresh_token(
    db: Session,
    token: RefreshToken,
) -> None:
    """
    Revoke a single refresh token.
    """

    token.revoked = True
    db.commit()


def revoke_all_refresh_tokens(
    db: Session,
    user_id: int,
) -> int:
    """
    Revoke every active refresh token for a user.

    Returns:
        Number of revoked sessions.
    """

    tokens = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked.is_(False),
        )
        .all()
    )

    for token in tokens:
        token.revoked = True

    db.commit()

    return len(tokens)


def delete_expired_tokens(
    db: Session,
) -> None:
    """
    Delete expired refresh tokens.
    """

    db.query(RefreshToken).filter(
        RefreshToken.expires_at < datetime.now(timezone.utc)
    ).delete()

    db.commit()


def list_active_tokens(
    db: Session,
    user_id: int,
) -> list[RefreshToken]:
    """
    Return every active (non-revoked, unexpired) refresh token for a user,
    newest first.
    """
    return (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked.is_(False),
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
        .order_by(RefreshToken.created_at.desc())
        .all()
    )
