"""
Provider-agnostic CRUD for encrypted integration credentials.

Keys are encrypted with :func:`app.core.encryption.encrypt_secret` before
persistence and decrypted only when the caller is about to make an outbound
request. No plaintext key ever touches the database, logs, or API responses.

Each row is scoped to ``(user_id, provider)``; the same storage is reused by
any future integration by passing a different ``provider`` value.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.encryption import decrypt_secret, encrypt_secret
from app.models.integration_credential import IntegrationCredential

NOT_CONFIGURED = "not_configured"


def get_credential(
    db: Session,
    user_id: int,
    provider: str = "virustotal",
) -> IntegrationCredential | None:
    """Return the stored credential row for a user/provider, if any."""
    return (
        db.query(IntegrationCredential)
        .filter(
            IntegrationCredential.user_id == user_id,
            IntegrationCredential.provider == provider,
        )
        .first()
    )


def get_api_key(
    db: Session,
    user_id: int,
    provider: str = "virustotal",
) -> str | None:
    """Decrypt and return the stored API key, or ``None`` if not configured."""
    credential = get_credential(db, user_id, provider)

    if credential is None:
        return None

    return decrypt_secret(credential.encrypted_api_key)


def upsert_api_key(
    db: Session,
    user_id: int,
    provider: str,
    api_key: str,
    *,
    status: str = "connected",
    last_tested_at: datetime | None = None,
) -> IntegrationCredential:
    """Encrypt and store a key, creating or updating the row in place."""
    encrypted = encrypt_secret(api_key)
    now = datetime.now(UTC)

    credential = get_credential(db, user_id, provider)

    if credential is None:
        credential = IntegrationCredential(
            user_id=user_id,
            provider=provider,
            encrypted_api_key=encrypted,
            status=status,
            last_tested_at=last_tested_at or now,
        )
        db.add(credential)
    else:
        credential.encrypted_api_key = encrypted
        credential.status = status
        credential.last_tested_at = last_tested_at or now
        credential.updated_at = now

    db.commit()
    db.refresh(credential)
    return credential


def set_status(
    db: Session,
    credential: IntegrationCredential,
    status: str,
    *,
    last_tested_at: datetime | None = None,
) -> IntegrationCredential:
    """Persist the latest connection-test result on a credential row."""
    credential.status = status
    credential.last_tested_at = last_tested_at or datetime.now(UTC)
    credential.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(credential)
    return credential


def delete_credential(
    db: Session,
    user_id: int,
    provider: str = "virustotal",
) -> bool:
    """Remove a user's stored credential. Returns whether a row was deleted."""
    credential = get_credential(db, user_id, provider)

    if credential is None:
        return False

    db.delete(credential)
    db.commit()
    return True
