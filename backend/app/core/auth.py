from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import settings


def create_access_token(data: dict[str, Any]) -> str:
    """
    Create a signed JWT access token.
    """

    payload = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload.update(
        {
            "iss": settings.APP_NAME,
            "aud": "guardianx-api",
            "iat": datetime.now(timezone.utc),
            "exp": expire,
        }
    )

    return jwt.encode(
        payload,
        settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM,
    )


def verify_access_token(token: str) -> dict[str, Any]:
    """
    Verify a JWT access token and return its payload.

    Raises:
        InvalidTokenError: If the token is invalid, expired,
        has an incorrect issuer, or an incorrect audience.
    """

    payload = jwt.decode(
        token,
        settings.SECRET_KEY.get_secret_value(),
        algorithms=[settings.ALGORITHM],
        audience="guardianx-api",
        issuer=settings.APP_NAME,
    )

    return payload
