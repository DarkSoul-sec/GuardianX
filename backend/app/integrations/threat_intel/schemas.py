"""Pydantic response models for the Threat Intelligence Center."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AttackTechnique(BaseModel):
    id: str
    name: str
    tactics: list[str] = Field(default_factory=list)
    description: str = ""


class VendorAdvisory(BaseModel):
    source: str = ""
    url: str
    tags: list[str] = Field(default_factory=list)


class TrendingCve(BaseModel):
    id: str
    title: str
    description: str = ""
    severity: str = "UNKNOWN"
    cvss_score: float | None = None
    published: str | None = None
    last_modified: str | None = None
    vendor: str | None = None
    affected_vendors: list[str] = Field(default_factory=list)
    affected_products: list[str] = Field(default_factory=list)
    cwes: list[str] = Field(default_factory=list)
    epss_score: float | None = None
    epss_percentile: float | None = None
    exploited: bool = False
    kev_due_date: str | None = None
    guardianx_risk_score: int = 0
    threat_level: str = "UNKNOWN"
    exploit_status: str = "No known active exploitation"
    ai_summary: str = ""
    references: list[VendorAdvisory] = Field(default_factory=list)


class EpssHistoryPoint(BaseModel):
    date: str
    score: float
    percentile: float


class CveDetail(TrendingCve):
    attack_techniques: list[AttackTechnique] = Field(default_factory=list)
    advisories: list[VendorAdvisory] = Field(default_factory=list)
    epss_history: list[EpssHistoryPoint] = Field(default_factory=list)


class KevEntry(BaseModel):
    cve_id: str
    vendor: str = ""
    product: str = ""
    vulnerability_name: str = ""
    description: str = ""
    required_action: str = ""
    due_date: str | None = None
    date_added: str | None = None
    known_ransomware_campaign: bool = False


class SeverityCount(BaseModel):
    severity: str
    count: int


class EpssBucket(BaseModel):
    bucket: str
    count: int


class RiskTimelinePoint(BaseModel):
    date: str
    published_count: int
    avg_epss: float


class SourceStatus(BaseModel):
    source: str
    configured: bool = True
    healthy: bool = True


class ThreatIntelStats(BaseModel):
    total_cves: int
    critical: int
    high: int
    medium: int
    low: int
    exploited_count: int
    avg_epss: float
    severity_distribution: list[SeverityCount] = Field(default_factory=list)
    epss_distribution: list[EpssBucket] = Field(default_factory=list)
    risk_timeline: list[RiskTimelinePoint] = Field(default_factory=list)
    sources: list[SourceStatus] = Field(default_factory=list)


class TrendingResponse(BaseModel):
    window_days: int
    total: int
    items: list[TrendingCve] = Field(default_factory=list)


class ThreatIntelSearchResponse(BaseModel):
    query: str = ""
    severity: str | None = None
    year: int | None = None
    vendor: str | None = None
    exploited_only: bool = False
    sort: str = "published"
    total: int
    items: list[TrendingCve] = Field(default_factory=list)
