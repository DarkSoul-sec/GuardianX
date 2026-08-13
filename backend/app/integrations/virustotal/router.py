"""
REST endpoints for the VirusTotal BYOAPI connection workflow.

Every route is JWT-protected and operates only on the authenticated user's
own credentials. Keys are accepted, encrypted and stored — they are never
returned in any response.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.integrations.virustotal.schemas import (
    ConnectRequest,
    ConnectResponse,
    DisconnectResponse,
    IntegrationStatus,
    TestConnectionRequest,
    TestConnectionResponse,
)
from app.integrations.virustotal.service import (
    connect_api_key,
    disconnect_api_key,
    get_status,
    test_connection,
    test_stored_connection,
)
from app.models.user import User

router = APIRouter(
    prefix="/integrations/virustotal",
    tags=["Integrations"],
)


@router.get(
    "/status",
    response_model=IntegrationStatus,
    summary="VirusTotal connection status",
)
def virustotal_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return whether the user has a VirusTotal key and its last state."""
    return get_status(db, current_user.id)


@router.post(
    "/connect",
    response_model=ConnectResponse,
    summary="Validate and save a VirusTotal API key",
)
def virustotal_connect(
    request: ConnectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Test the submitted key against VirusTotal, then encrypt and store it.
    The key itself is never returned in the response.
    """
    status = connect_api_key(db, current_user.id, request.api_key)
    return ConnectResponse(status=status)


@router.post(
    "/test",
    response_model=TestConnectionResponse,
    summary="Test a VirusTotal API key",
)
def virustotal_test(
    request: TestConnectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Validate a candidate key (if provided) or the stored key, without
    persisting a candidate. The stored status is refreshed when testing the
    stored key.
    """
    if request.api_key is not None:
        result = test_connection(request.api_key)
        return TestConnectionResponse(
            status=IntegrationStatus(
                provider="virustotal",
                configured=get_status(db, current_user.id).configured,
                status=result.status,
                message=result.message,
            )
        )

    return TestConnectionResponse(
        status=test_stored_connection(db, current_user.id)
    )


@router.delete(
    "/disconnect",
    response_model=DisconnectResponse,
    summary="Remove the VirusTotal API key",
)
def virustotal_disconnect(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Permanently remove the user's stored VirusTotal API key."""
    return DisconnectResponse(
        disconnected=disconnect_api_key(db, current_user.id)
    )
