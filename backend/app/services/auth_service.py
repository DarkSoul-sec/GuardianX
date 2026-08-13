from pwdlib.exceptions import UnknownHashError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.roles import UserRole
from app.core.security import (
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.logger import logger
from app.schemas.auth import AdminSetupRequest
from app.schemas.user import (
    UserCreate,
    UserUpdate,
)


def email_verification_required() -> bool:
    """Whether email verification gates authentication for this deployment.

    In ``local`` mode a user is trusted through physical/administrative
    control of the installation, so an unverified email is not a login
    blocker. ``cloud`` mode keeps the strict verified-email requirement.
    """
    return settings.AUTH_MODE == "cloud"


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    return (
        db.query(User)
        .filter(User.email == email)
        .first()
    )


def admin_exists(db: Session) -> bool:
    """Return True when at least one ADMIN user exists.

    This is the authoritative "is GuardianX initialized?" signal. It is
    derived purely from database state, never from client-side hints.
    """
    return (
        db.query(User.id)
        .filter(User.role == UserRole.ADMIN)
        .first()
        is not None
    )


def get_user_by_username(
    db: Session,
    username: str,
) -> User | None:
    return (
        db.query(User)
        .filter(User.username == username)
        .first()
    )


def get_user_by_id(
    db: Session,
    user_id: int,
) -> User | None:
    return (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )


def get_all_users(
    db: Session,
) -> list[User]:
    return db.query(User).all()


def create_user(
    db: Session,
    user: UserCreate,
    *,
    is_active: bool = False,
    commit: bool = True,
) -> User:
    """Create a user in a pending, unverified state.

    ``is_active`` defaults to ``False`` so a freshly registered account is
    never usable until email verification flips it on. ``commit=False`` lets
    callers (e.g. signup) group user + token creation into a single
    transaction that can be rolled back atomically if email delivery fails.
    """
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=get_password_hash(
            user.password,
        ),
        role=UserRole.USER,
        is_active=is_active,
    )

    db.add(db_user)

    if commit:
        db.commit()
        db.refresh(db_user)
    else:
        db.flush()

    return db_user


def create_admin_user(
    db: Session,
    data: AdminSetupRequest,
    *,
    commit: bool = True,
) -> User:
    """Create the first-run local administrator.

    The administrator is immediately active, is granted the ADMIN role and
    needs no email address or verification token: trust comes from having
    administrative control over the installation. The password is hashed with
    the same secure scheme used everywhere else and is never stored in
    plaintext.
    """
    db_admin = User(
        username=data.username,
        email=None,
        password_hash=get_password_hash(data.password),
        role=UserRole.ADMIN,
        is_active=True,
        email_verified=False,
    )

    db.add(db_admin)

    if commit:
        db.commit()
        db.refresh(db_admin)
    else:
        db.flush()

    return db_admin


def authenticate_user(
    db: Session,
    identifier: str,
    password: str,
) -> User | None:
    """Authenticate an active, email-verified user by email address or username."""

    user = get_user_by_email(db, identifier)

    if user is None:
        user = get_user_by_username(db, identifier)

    if user is None:
        return None

    if not user.is_active:
        logger.warning("Authentication attempt for inactive user: %s", user.id)
        return None

    if email_verification_required() and not user.email_verified:
        logger.warning(
            "Authentication attempt for unverified user: %s", user.id
        )
        return None

    try:
        password_matches = verify_password(
            password,
            user.password_hash,
        )
    except UnknownHashError:
        logger.error("User %s has an unsupported password hash.", user.id)
        return None

    if not password_matches:
        return None

    return user


def update_user(
    db: Session,
    user: User,
    data: UserUpdate,
) -> User:
    update_data = data.model_dump(
        exclude_unset=True,
    )

    for key, value in update_data.items():
        setattr(
            user,
            key,
            value,
        )

    db.commit()
    db.refresh(user)

    return user


def update_user_password(
    db: Session,
    user: User,
    new_password: str,
) -> User:
    user.password_hash = get_password_hash(new_password)

    db.commit()
    db.refresh(user)

    return user


def update_user_role(
    db: Session,
    user: User,
    role: UserRole,
) -> User:
    user.role = role

    db.commit()
    db.refresh(user)

    return user


def update_user_status(
    db: Session,
    user: User,
    is_active: bool,
) -> User:
    user.is_active = is_active

    db.commit()
    db.refresh(user)

    return user


def delete_user(
    db: Session,
    user: User,
) -> None:
    db.delete(user)
    db.commit()
