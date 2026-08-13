"""
REST endpoints for the Threat Intelligence platform.

Every route is JWT-protected and operates only on the authenticated user's own
data. Provider credentials are decrypted server-side and never appear in any
response; the raw VirusTotal payload is normalized before leaving the service
layer.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError
from app.database.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.intelligence.schemas import (
    DeleteHistoryResponse,
    IntelligenceHistoryResponse,
    IntelligenceLookupResponse,
    IntelligenceStatus,
    LookupRequest,
    IOCType,
)
from app.intelligence import service
from app.models.user import User

router = APIRouter(
    prefix="/intelligence",
    tags=["Threat Intelligence"],
)


@router.post(
    "/lookup",
    response_model=IntelligenceLookupResponse,
    summary="Analyze an IP, domain, URL or SHA256 hash",
)
def intelligence_lookup(
    request: LookupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Run the IOC search workflow: detect the indicator type, query the provider
    (cached for 24 hours), normalize the report, and record search history.
    """
    return service.lookup(db, current_user.id, request.value)


@router.get(
    "/history",
    response_model=IntelligenceHistoryResponse,
    summary="List search history",
)
def intelligence_history(
    ioc_type: IOCType | None = Query(default=None),
    q: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the user's past IOC searches, newest first, with filters."""
    return service.list_history(
        db,
        current_user.id,
        ioc_type=ioc_type,
        query=q,
        page=page,
        limit=limit,
    )


@router.delete(
    "/history",
    response_model=DeleteHistoryResponse,
    summary="Clear all search history",
)
def intelligence_history_clear(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete every search-history entry for the authenticated user."""
    deleted = service.clear_history(db, current_user.id)
    return DeleteHistoryResponse(deleted=deleted > 0)


@router.delete(
    "/history/{history_id}",
    response_model=DeleteHistoryResponse,
    summary="Delete one search-history entry",
)
def intelligence_history_delete(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a single history entry owned by the authenticated user."""
    if not service.delete_history(db, current_user.id, history_id):
        raise ResourceNotFoundError("The search history entry was not found.")
    return DeleteHistoryResponse(deleted=True)


@router.get(
    "/status",
    response_model=IntelligenceStatus,
    summary="Threat Intelligence provider status",
)
def intelligence_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return whether the provider (VirusTotal) is configured for the user."""
    return service.status(db, current_user.id)
