"""
Symmetric encryption for stored secrets (API keys, tokens).

Secrets are encrypted with Fernet before they are persisted and decrypted
only in memory at the moment they are used. The encryption key is derived
from the deployment ``SECRET_KEY`` so no additional key material has to be
managed at runtime. Plaintext secrets must never be logged or returned to
clients.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class SecretEncryptionError(Exception):
    """A stored secret could not be decrypted or validated."""


def _fernet() -> Fernet:
    secret = settings.SECRET_KEY.get_secret_value()

    key = base64.urlsafe_b64encode(
        hashlib.sha256(secret.encode("utf-8")).digest()
    )

    return Fernet(key)


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a plaintext secret for storage."""
    if not plaintext:
        raise ValueError("Cannot encrypt an empty secret.")

    return _fernet().encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_secret(token: str) -> str:
    """Decrypt a stored secret back into memory-only plaintext."""
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError) as exc:
        raise SecretEncryptionError(
            "The stored secret could not be decrypted."
        ) from exc
