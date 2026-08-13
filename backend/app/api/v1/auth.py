import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.auth import create_access_token
from app.core.config import settings
from app.database.dependencies import get_db
from app.logger import logger
from app.schemas.auth import (
    AdminSetupRequest,
    EmailVerificationRequest,
    ForgotPasswordRequest,
    MessageResponse,
    PasswordResetRequest,
    ResendVerificationRequest,
    SetupStatusResponse,
)
from app.schemas.token import RefreshTokenRequest
from app.schemas.user import (
    Token,
    UserCreate,
    UserResponse,
)
from app.services.auth_service import (
    admin_exists,
    authenticate_user,
    create_admin_user,
    create_user,
    get_user_by_email,
    get_user_by_username,
    update_user_password,
)
from app.services.activity_service import record_activity
from app.services.email_token_service import (
    KIND_RESET_PASSWORD,
    KIND_VERIFY_EMAIL,
    consume_email_token,
    create_email_token,
    revoke_email_tokens,
)
from app.services.mail_service import (
    DeliveryResult,
    build_link,
    send_mail,
)
from app.services.mail_templates import (
    build_reset_email,
    build_verification_email,
    build_welcome_email,
)
from app.services.token_service import (
    generate_refresh_token,
    get_refresh_token,
    revoke_all_refresh_tokens,
    revoke_refresh_token,
    store_refresh_token,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.get(
    "/setup-status",
    response_model=SetupStatusResponse,
)
def setup_status(
    db: Session = Depends(get_db),
):
    """
    Report whether GuardianX has been initialized.

    ``initialized`` is computed from database state (an ADMIN user exists),
    never from client-side hints. A fresh installation returns
    ``{"initialized": false, "auth_mode": "local"}``.
    """
    return SetupStatusResponse(
        initialized=admin_exists(db),
        auth_mode=settings.AUTH_MODE,
    )


@router.post(
    "/setup",
    response_model=MessageResponse,
)
def setup(
    payload: AdminSetupRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    First-run setup: create the initial local administrator.

    Permanently unavailable once an administrator exists. The database state
    is re-checked here, so calling this endpoint repeatedly can never create
    a second administrator.
    """
    if admin_exists(db):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="GuardianX has already been initialized.",
        )

    if get_user_by_username(db, payload.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken.",
        )

    admin = create_admin_user(db, payload, commit=False)

    client_ip = request.client.host if request.client else None
    record_activity(
        db,
        user_id=admin.id,
        action="setup",
        detail=f"GuardianX initialized with administrator {admin.username}",
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent"),
    )

    db.commit()

    return MessageResponse(
        message="GuardianX initialized successfully.",
    )


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    if settings.AUTH_MODE == "local":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Public registration is disabled on this installation. Use "
                "the first-run setup to create the local administrator."
            ),
        )

    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )

    if get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken.",
        )

    # Create the account in a pending, unverified state. The user and its
    # verification token are written to one transaction that is only committed
    # after the verification email has been accepted by a real SMTP server. If
    # delivery is unavailable or fails, the whole registration is rolled back
    # so we never report a success (or "check your inbox") that did not happen,
    # and no orphaned unverified account blocks a clean retry.
    user = create_user(db, user_data, commit=False)

    correlation_id = uuid.uuid4().hex

    try:
        delivery = _send_verification_email(
            db,
            user,
            commit_token=False,
            correlation_id=correlation_id,
        )
    except Exception:
        db.rollback()
        logger.exception(
            "Failed to send verification email to %s (correlation_id=%s); "
            "registration rolled back.",
            user_data.email,
            correlation_id,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "We could not send your verification email. Please try again "
                "later."
            ),
        )

    if not delivery.delivered:
        # SMTP is not configured (log-only mode) — no real message was sent,
        # so this must not be reported as a successful signup/email dispatch.
        db.rollback()
        logger.error(
            "Verification email not delivered for %s: mode=%s "
            "correlation_id=%s; registration rolled back.",
            user_data.email,
            delivery.mode,
            correlation_id,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The verification email service is not configured. Please "
                "contact the administrator."
            ),
        )

    client_ip = request.client.host if request.client else None
    record_activity(
        db,
        user_id=user.id,
        action="signup",
        detail=f"Account created for {user.username}",
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent"),
    )

    db.commit()

    _send_welcome_email(db, user)

    return user


@router.post(
    "/login",
    response_model=Token,
)
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db,
        username,
        password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    user.last_login = datetime.now(timezone.utc)

    client_ip = request.client.host if request.client else None
    record_activity(
        db,
        user_id=user.id,
        action="login",
        detail=f"Signed in as {user.username}",
        ip_address=client_ip,
        user_agent=request.headers.get("user-agent"),
    )

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "username": user.username,
            "type": "access",
        }
    )

    refresh_token = generate_refresh_token()

    store_refresh_token(
        db=db,
        user_id=user.id,
        refresh_token=refresh_token,
        user_agent=request.headers.get("user-agent"),
        ip_address=client_ip,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
    payload: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Revoke the presented refresh token, terminating the session server-side.

    Best-effort: unknown or already-revoked tokens still return 204 so the
    client can always clear its local session.
    """
    stored = get_refresh_token(db, payload.refresh_token)

    if stored is not None:
        revoke_refresh_token(db, stored)
        user_id = stored.user_id if stored.user_id is not None else None
    else:
        user_id = None

    if user_id is not None:
        client_ip = request.client.host if request.client else None
        record_activity(
            db,
            user_id=user_id,
            action="logout",
            detail="Signed out",
            ip_address=client_ip,
            user_agent=request.headers.get("user-agent"),
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _send_verification_email(
    db: Session,
    user,
    *,
    revoke_previous: bool = False,
    commit_token: bool = True,
    correlation_id: str | None = None,
) -> DeliveryResult:
    """Create a verification token and email it to a user.

    Returns the mailer's :class:`DeliveryResult`. A ``delivered=False`` result
    means no real SMTP delivery happened (e.g. log-only development mode) and
    the caller must not report the email as sent. Delivery failures are **not**
    swallowed: the underlying exception propagates so callers can log the real
    cause and react (roll back a pending signup, return an error, etc.).
    ``revoke_previous`` marks any outstanding verification tokens used before
    issuing a new one (single-use guarantee on resend).
    """
    if revoke_previous:
        revoke_email_tokens(db, user.id, KIND_VERIFY_EMAIL)

    token = create_email_token(
        db,
        user.id,
        KIND_VERIFY_EMAIL,
        commit=commit_token,
    )

    link = build_link(f"/verify-email?token={token}")

    content = build_verification_email(
        username=user.username,
        verify_url=link,
        expires_minutes=settings.EMAIL_VERIFICATION_EXPIRE_MINUTES,
    )

    correlation_id = correlation_id or uuid.uuid4().hex

    return send_mail(
        user.email,
        content.subject,
        content.text,
        html_body=content.html,
        email_type="verification",
        correlation_id=correlation_id,
    )


def _send_welcome_email(db: Session, user) -> None:
    """Send a non-essential welcome email on signup (best-effort)."""
    content = build_welcome_email(username=user.username)

    try:
        send_mail(
            user.email,
            content.subject,
            content.text,
            html_body=content.html,
            email_type="welcome",
            correlation_id=uuid.uuid4().hex,
        )
    except Exception:
        logger.exception("Failed to send welcome email to %s", user.email)


@router.post(
    "/verify-email",
    response_model=MessageResponse,
)
def verify_email(
    payload: EmailVerificationRequest,
    db: Session = Depends(get_db),
):
    """Confirm an email address using a one-time verification token."""
    email_token = consume_email_token(
        db,
        payload.token,
        KIND_VERIFY_EMAIL,
    )

    if email_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid, expired, or already-used verification token.",
        )

    user = email_token.user

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User no longer exists.",
        )

    if user.email_verified:
        return MessageResponse(
            message="Email address is already verified.",
        )

    # Activation is tied to verification: only a successful token check turns
    # the account active. Never trust a frontend-supplied verification flag.
    user.email_verified = True
    user.is_active = True
    db.commit()

    record_activity(
        db,
        user_id=user.id,
        action="verify_email",
        detail="Email address verified",
    )

    return MessageResponse(
        message="Email verified successfully.",
    )


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
)
def resend_verification(
    payload: ResendVerificationRequest,
    db: Session = Depends(get_db),
):
    """Resend the verification email for an account.

    Revokes any previously issued verification tokens (single-use guarantee),
    issues a fresh one and delivers it. Delivery failures are surfaced as a
    ``502``, and an unconfigured (log-only) mail service as a ``503``, so the
    caller is never told an email was sent when it was not. Unknown emails
    keep the enumeration-safe generic message.
    """
    user = get_user_by_email(db, payload.email)

    if user is not None and not user.email_verified:
        try:
            delivery = _send_verification_email(
                db,
                user,
                revoke_previous=True,
            )
        except Exception:
            logger.exception(
                "Failed to resend verification email to %s.",
                payload.email,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    "We could not send your verification email. Please try "
                    "again later."
                ),
            )

        if not delivery.delivered:
            logger.error(
                "Resend verification email not delivered for %s: mode=%s.",
                payload.email,
                delivery.mode,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "The verification email service is not configured. Please "
                    "contact the administrator."
                ),
            )

    return MessageResponse(
        message="If that email is registered, a verification link has been sent.",
    )


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
)
def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Request a password-reset link for an account.

    Returns the same response whether or not the email exists to avoid user
    enumeration.
    """
    user = get_user_by_email(db, payload.email)

    if user is not None and user.is_active:
        revoke_email_tokens(db, user.id, KIND_RESET_PASSWORD)

        token = create_email_token(
            db,
            user.id,
            KIND_RESET_PASSWORD,
        )

        link = build_link(f"/reset-password?token={token}")

        content = build_reset_email(
            username=user.username,
            reset_url=link,
            expires_minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES,
        )

        correlation_id = uuid.uuid4().hex

        try:
            send_mail(
                user.email,
                content.subject,
                content.text,
                html_body=content.html,
                email_type="password_reset",
                correlation_id=correlation_id,
            )
        except Exception:
            logger.exception(
                "Failed to send password-reset email to %s (correlation_id=%s)",
                user.email,
                correlation_id,
            )

        client_ip = request.client.host if request.client else None
        record_activity(
            db,
            user_id=user.id,
            action="forgot_password",
            detail="Password reset requested",
            ip_address=client_ip,
            user_agent=request.headers.get("user-agent"),
        )

    return MessageResponse(
        message="If that email is registered, a reset link has been sent.",
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
)
def reset_password(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    """Set a new password using a valid reset token.

    On success all sessions are revoked, forcing a fresh login everywhere.
    """
    email_token = consume_email_token(
        db,
        payload.token,
        KIND_RESET_PASSWORD,
    )

    if email_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid, expired, or already-used reset token.",
        )

    user = email_token.user

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User no longer exists.",
        )

    update_user_password(
        db,
        user,
        payload.new_password,
    )

    revoke_all_refresh_tokens(db, user.id)

    record_activity(
        db,
        user_id=user.id,
        action="reset_password",
        detail="Password reset completed",
    )

    return MessageResponse(
        message="Password reset successfully. Your other sessions were signed out.",
    )


@router.post(
    "/refresh",
    response_model=Token,
)
def refresh(
    payload: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Rotate a refresh token into a fresh access token pair.

    The presented refresh token is revoked and replaced with a new one
    (rotation), so a stolen token can only be used once.
    """
    stored = get_refresh_token(db, payload.refresh_token)

    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked refresh token.",
        )

    expires_at = stored.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= datetime.now(timezone.utc):
        revoke_refresh_token(db, stored)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired.",
        )

    user = stored.user

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is no longer active.",
        )

    if settings.AUTH_MODE == "cloud" and not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is no longer active.",
        )

    revoke_refresh_token(db, stored)

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "username": user.username,
            "type": "access",
        }
    )

    refresh_token = generate_refresh_token()

    client_ip = request.client.host if request.client else None

    store_refresh_token(
        db=db,
        user_id=user.id,
        refresh_token=refresh_token,
        user_agent=request.headers.get("user-agent"),
        ip_address=client_ip,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
