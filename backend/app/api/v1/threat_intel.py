from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import get_current_user
from app.integrations.threat_intel.schemas import (
    AttackTechnique,
    CveDetail,
    KevEntry,
    ThreatIntelSearchResponse,
    ThreatIntelStats,
    TrendingResponse,
)
from app.integrations.threat_intel.service import (
    get_attack_techniques,
    get_cve_detail,
    get_kev_catalog,
    get_stats,
    get_trending,
    search_cves,
)
from app.models.user import User

router = APIRouter(
    prefix="/threat-intel",
    tags=["Threat Intelligence"],
)


@router.get(
    "/trending",
    response_model=TrendingResponse,
    summary="Trending CVEs",
)
def trending(
    days: int = Query(14, ge=1, le=90),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    return get_trending(days=days, limit=limit)


@router.get(
    "/search",
    response_model=ThreatIntelSearchResponse,
    summary="Search CVEs with filters",
)
def search(
    q: str | None = Query(None, max_length=200),
    severity: str | None = Query(None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$"),
    year: int | None = Query(None, ge=1999, le=2100),
    vendor: str | None = Query(None, max_length=100),
    exploited: bool = Query(False),
    sort: str = Query("published", pattern="^(published|epss|risk)$"),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    return search_cves(
        query=q,
        severity=severity,
        year=year,
        vendor=vendor,
        exploited_only=exploited,
        sort_by=sort,
        limit=limit,
    )


@router.get(
    "/cve/{cve_id}",
    response_model=CveDetail,
    summary="CVE detail with exploit intelligence",
)
def cve_detail(
    cve_id: str,
    current_user: User = Depends(get_current_user),
):
    return get_cve_detail(cve_id)


@router.get(
    "/stats",
    response_model=ThreatIntelStats,
    summary="Threat intelligence dashboard stats",
)
def stats(
    days: int = Query(14, ge=1, le=60),
    current_user: User = Depends(get_current_user),
):
    return get_stats(days=days)


@router.get(
    "/kev",
    response_model=list[KevEntry],
    summary="CISA KEV catalog",
)
def kev_catalog(
    limit: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    return get_kev_catalog(limit=limit)


@router.get(
    "/attack-techniques",
    response_model=list[AttackTechnique],
    summary="MITRE ATT&CK techniques",
)
def attack_techniques(
    tactic: str | None = Query(None, max_length=80),
    current_user: User = Depends(get_current_user),
):
    return get_attack_techniques(tactic=tactic)
