from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.integrations.virustotal.schemas import (
    IntelligenceRequest,
    VirusTotalLookupResponse,
)
from app.integrations.virustotal.service import (
    get_configured_api_key,
    lookup_domain,
    lookup_file_hash,
    lookup_ip,
    lookup_url,
)
from app.models.user import User

router = APIRouter(
    prefix="/intelligence",
    tags=["Threat Intelligence"],
)


@router.post(
    "/url",
    response_model=VirusTotalLookupResponse,
    summary="URL reputation lookup",
)
def intelligence_url(
    request: IntelligenceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    api_key = get_configured_api_key(db, current_user.id)
    return lookup_url(api_key, request.value)


@router.post(
    "/domain",
    response_model=VirusTotalLookupResponse,
    summary="Domain reputation lookup",
)
def intelligence_domain(
    request: IntelligenceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    api_key = get_configured_api_key(db, current_user.id)
    return lookup_domain(api_key, request.value)


@router.post(
    "/ip",
    response_model=VirusTotalLookupResponse,
    summary="IP reputation lookup",
)
def intelligence_ip(
    request: IntelligenceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    api_key = get_configured_api_key(db, current_user.id)
    return lookup_ip(api_key, request.value)


@router.post(
    "/hash",
    response_model=VirusTotalLookupResponse,
    summary="SHA256 file hash lookup",
)
def intelligence_hash(
    request: IntelligenceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    api_key = get_configured_api_key(db, current_user.id)
    return lookup_file_hash(api_key, request.value)
