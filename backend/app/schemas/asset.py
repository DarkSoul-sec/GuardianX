from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.asset_types import AssetType
from app.core.network import validate_scan_target


def _validate_target_field(value):
    if value is None or not str(value).strip():
        return value

    return validate_scan_target(value)


class AssetCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    asset_type: AssetType

    ip_address: str | None = None
    domain: str | None = None
    operating_system: str | None = None
    environment: str | None = None
    owner: str | None = None
    criticality: str | None = None
    description: str | None = None

    _validate_target = field_validator(
        "ip_address",
        "domain",
        mode="before",
    )(_validate_target_field)


class AssetUpdate(BaseModel):
    name: str | None = None
    asset_type: AssetType | None = None

    ip_address: str | None = None
    domain: str | None = None
    operating_system: str | None = None
    environment: str | None = None
    owner: str | None = None
    criticality: str | None = None
    description: str | None = None

    _validate_target = field_validator(
        "ip_address",
        "domain",
        mode="before",
    )(_validate_target_field)


class AssetResponse(BaseModel):
    id: int

    name: str
    asset_type: AssetType

    ip_address: str | None
    domain: str | None
    operating_system: str | None
    environment: str | None
    owner: str | None
    criticality: str | None
    description: str | None

    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class AssetServiceItem(BaseModel):
    port: int
    protocol: str
    product: str | None = None
    version: str | None = None
    cpe: str | None = None
    state: str


class AssetRecentScanItem(BaseModel):
    scan_id: int
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    total_findings: int = 0


class AssetRecentFindingItem(BaseModel):
    cve: str | None = None
    severity: str
    title: str
    status: str
    recommendation: str | None = None
    cvss: float | None = None


class AssetDetailResponse(BaseModel):
    id: int
    name: str
    hostname: str | None = None
    ip_address: str | None = None
    asset_type: AssetType
    domain: str | None = None
    operating_system: str | None = None
    environment: str | None = None
    owner: str | None = None
    criticality: str | None = None
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    risk_score: int = 0
    security_score: int = 0
    total_findings: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0

    attack_surface_score: int = 0
    internet_facing: bool = False
    open_ports: list[int] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    ai_summary: str = ""

    services: list[AssetServiceItem] = Field(default_factory=list)
    recent_scans: list[AssetRecentScanItem] = Field(default_factory=list)
    recent_findings: list[AssetRecentFindingItem] = Field(default_factory=list)

    model_config = ConfigDict(
        from_attributes=True,
    )
