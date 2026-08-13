from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.roles import UserRole
from app.core.security import verify_password
from app.database.dependencies import get_db
from app.dependencies.auth import (
    get_current_user,
    require_role,
)
from app.logger import logger
from app.models.user import User
from app.schemas.session import SessionListResponse, SessionResponse
from app.schemas.user import (
    RoleUpdate,
    UserPasswordChange,
    UserResponse,
    UserStatusUpdate,
    UserUpdate,
)
from app.services.token_service import (
    list_active_tokens,
    revoke_all_refresh_tokens,
    revoke_refresh_token,
)
from app.services.auth_service import (
    delete_user,
    get_all_users,
    get_user_by_id,
    update_user,
    update_user_password,
    update_user_role,
    update_user_status,
)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    """
    Return the authenticated user.
    """
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
)
def update_me(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update the authenticated user's own profile.
    """
    return update_user(
        db=db,
        user=current_user,
        data=data,
    )


@router.post(
    "/me/password",
    response_model=UserResponse,
)
def change_my_password(
    data: UserPasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Change the authenticated user's own password.
    """
    try:
        password_matches = verify_password(
            data.current_password,
            current_user.password_hash,
        )
    except (ValueError, TypeError):
        logger.warning(
            "Password verification failed for user %s.",
            current_user.id,
        )
        password_matches = False

    if not password_matches:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    user = update_user_password(
        db=db,
        user=current_user,
        new_password=data.new_password,
    )

    revoked = revoke_all_refresh_tokens(
        db,
        current_user.id,
    )

    if revoked:
        logger.info(
            "Revoked %s refresh token(s) after password change for user %s.",
            revoked,
            current_user.id,
        )

    return user


@router.get(
    "/me/sessions",
    response_model=SessionListResponse,
)
def list_my_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List the authenticated user's active sessions.
    """
    tokens = list_active_tokens(db, current_user.id)

    return SessionListResponse(
        sessions=[SessionResponse.model_validate(t) for t in tokens],
    )


@router.post(
    "/me/sessions/revoke-all",
    response_model=SessionListResponse,
)
def revoke_my_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Revoke all of the authenticated user's active sessions, signing them out
    of every device.
    """
    revoke_all_refresh_tokens(db, current_user.id)

    return SessionListResponse(sessions=[])


@router.delete(
    "/me/sessions/{token_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def revoke_my_session(
    token_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Revoke a single active session belonging to the current user.
    """
    tokens = list_active_tokens(db, current_user.id)
    target = next((t for t in tokens if t.id == token_id), None)

    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    revoke_refresh_token(db, target)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "",
    response_model=List[UserResponse],
)
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
):
    """
    Admin only.
    Return all users.
    """
    return get_all_users(db)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
):
    user = get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return user


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
)
def edit_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
):
    user = get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return update_user(
        db,
        user,
        data,
    )


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
)
def change_role(
    user_id: int,
    data: RoleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
):
    user = get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return update_user_role(
        db,
        user,
        data.role,
    )


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
)
def change_status(
    user_id: int,
    data: UserStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
):
    user = get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return update_user_status(
        db,
        user,
        data.is_active,
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
):
    user = get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    delete_user(
        db,
        user,
    )

    return None
