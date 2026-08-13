from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.auth import verify_access_token
from app.core.config import settings
from app.core.roles import UserRole
from app.database.dependencies import get_db
from app.logger import logger
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = verify_access_token(token)
    except InvalidTokenError:
        logger.debug(
            "Rejected invalid JWT (garbage, malformed, expired or "
            "badly-signed).",
        )
        raise _unauthorized("Invalid or expired token.")

    user_id = payload.get("sub")

    if user_id is None:
        raise _unauthorized("Invalid authentication token.")

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise _unauthorized("Invalid authentication token.")

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        logger.warning(
            "Token for unknown user_id=%s rejected.",
            user_id,
        )
        raise _unauthorized("User not found.")

    if not user.is_active:
        raise _unauthorized("User account is inactive.")

    if settings.AUTH_MODE == "cloud" and not user.email_verified:
        raise _unauthorized("Email address is not verified.")

    if payload.get("type") != "access":
        logger.warning(
            "Rejected non-access token (type=%s) on protected route.",
            payload.get("type"),
        )
        raise _unauthorized("Invalid token type.")

    logger.debug(
        "Authenticated user=%s id=%s role=%s",
        user.username,
        user.id,
        user.role,
    )

    return user


def require_role(*roles: UserRole) -> Callable:
    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        return current_user

    return role_checker
