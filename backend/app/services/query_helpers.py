"""
Shared query helper utilities.

This module centralizes common query patterns used across GuardianX
services to reduce duplication and keep authorization logic consistent.
"""

from __future__ import annotations

from sqlalchemy.orm import Query

from app.core.roles import UserRole
from app.models.asset import Asset
from app.models.user import User


def apply_asset_scope(
    query: Query,
    current_user: User,
) -> Query:
    """
    Restrict Asset-based queries to the requesting user.

    Administrators can access every asset.
    Standard users can only access assets they created.
    """

    if current_user.role == UserRole.ADMIN:
        return query

    return query.filter(
        Asset.created_by == current_user.id,
    )
