from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FindingReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cve: str | None = None
    title: str
    severity: str
    cvss: float | None = None
    status: str
    description: str | None = None
    recommendation: str | None = None
    affected_service: str | None = None


class ServiceReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    port: int
    protocol: str | None = None
    service: str | None = None
    product: str | None = None
    version: str | None = None
    state: str | None = None
    cpe: str | None = None


class AssetReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str

    domain: str | None = None
    ip_address: str | None = None
    asset_type: str | None = None

    risk_score: int

    critical: int
    high: int
    medium: int
    low: int

    total_findings: int

    last_scan: datetime | None = None
    scanner: str | None = None

    services: list[ServiceReport]
    findings: list[FindingReport]


class ScanSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None


class ExecutiveSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    assets: int
    scans: int

   
    critical: int
    high: int
    medium: int
    low: int

    total_findings: int
    risk_score: int


class ExecutiveReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    generated_at: datetime

    summary: ExecutiveSummary

    top_assets: list[AssetReport]

    recommendations: list[str]


class TechnicalReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    generated_at: datetime

    scan: ScanSummary

    asset: AssetReport

    findings: list[FindingReport]
