from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.integrations.virustotal.schemas import VirusTotalLookupResponse
from app.integrations.virustotal.service import (
    get_configured_api_key,
    lookup_domain,
    lookup_file_hash,
    lookup_ip,
    lookup_url,
)
from app.models.user import User

router = APIRouter(
    prefix="/virustotal",
    tags=["VirusTotal"],
)


@router.get(
    "/url",
    response_model=VirusTotalLookupResponse,
    summary="URL reputation",
)
def get_url_reputation(
    url: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    api_key = get_configured_api_key(db, current_user.id)
    return lookup_url(api_key, url)


@router.get(
    "/domain/{domain}",
    response_model=VirusTotalLookupResponse,
    summary="Domain reputation",
)
def get_domain_reputation(
    domain: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    api_key = get_configured_api_key(db, current_user.id)
    return lookup_domain(api_key, domain)


@router.get(
    "/ip/{ip_address}",
    response_model=VirusTotalLookupResponse,
    summary="IP reputation",
)
def get_ip_reputation(
    ip_address: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    api_key = get_configured_api_key(db, current_user.id)
    return lookup_ip(api_key, ip_address)


@router.get(
    "/file/{sha256}",
    response_model=VirusTotalLookupResponse,
    summary="SHA256 file hash lookup",
)
def get_file_hash_reputation(
    sha256: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    api_key = get_configured_api_key(db, current_user.id)
    return lookup_file_hash(api_key, sha256)
