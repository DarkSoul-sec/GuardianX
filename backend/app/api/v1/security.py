"""
Public security configuration surfaced to the frontend.

Only non-sensitive flags are exposed — never secrets. The frontend uses
``private_network_scanning_enabled`` to show the "Development Mode" warning
banner when the backend is configured to permit private-network scanning.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(
    prefix="/security",
    tags=["Security"],
)


@router.get(
    "/config",
    summary="Non-sensitive security configuration",
)
def security_config() -> dict[str, bool]:
    """
    Return boolean security flags safe to expose to clients.

    ``private_network_scanning_enabled`` is true only when the operator
    explicitly enabled ``ALLOW_PRIVATE_NETWORK_SCANS`` for local development.
    """
    return {
        "private_network_scanning_enabled": (
            settings.ALLOW_PRIVATE_NETWORK_SCANS
        ),
    }
