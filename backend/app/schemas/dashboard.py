from datetime import datetime

from pydantic import BaseModel, Field


class DashboardResponse(BaseModel):
    total_assets: int
    total_scans: int
    pending_scans: int
    running_scans: int
    completed_scans: int
    failed_scans: int
    open_ports: int
    last_scan: datetime | None


class RecentScanItem(BaseModel):
    scan_id: int
    asset_name: str
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    finding_count: int = 0


class TopVulnerableAssetItem(BaseModel):
    asset_id: int
    asset_name: str
    risk_score: int
    total_findings: int
    critical_findings: int


class RecentFindingItem(BaseModel):
    cve: str | None
    title: str
    severity: str
    asset: str
    created_at: datetime
    status: str


class RiskTrendItem(BaseModel):
    date: str
    score: int


class AssetGrowthItem(BaseModel):
    date: str
    count: int


class AssetDistributionItem(BaseModel):
    type: str
    count: int


class FindingsTrendItem(BaseModel):
    date: str
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class TopVulnerabilityItem(BaseModel):
    cve: str | None = None
    title: str
    severity: str
    cvss: float | None = None
    status: str
    asset: str


class DashboardOverviewResponse(BaseModel):
    assets: int = 0
    completed_scans: int = 0
    open_ports: int = 0
    total_services: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    total_findings: int = 0
    risk_score: int = 0
    risk_trend: list[RiskTrendItem] = Field(default_factory=list)
    asset_growth: list[AssetGrowthItem] = Field(default_factory=list)
    asset_distribution: list[AssetDistributionItem] = Field(default_factory=list)
    findings_trend: list[FindingsTrendItem] = Field(default_factory=list)
    top_vulnerabilities: list[TopVulnerabilityItem] = Field(default_factory=list)
    recent_scans: list[RecentScanItem] = Field(default_factory=list)
    top_vulnerable_assets: list[TopVulnerableAssetItem] = Field(default_factory=list)
    recent_findings: list[RecentFindingItem] = Field(default_factory=list)
