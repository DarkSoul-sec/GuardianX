from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.scan_profile import ScanProfile
from app.core.scan_status import ScanStatus


class ScanCreate(BaseModel):
    asset_id: int
    scan_profile: ScanProfile = ScanProfile.STANDARD


class ScanResponse(BaseModel):
    id: int
    asset_id: int
    asset_name: str | None = None
    status: ScanStatus
    scanner: str
    scan_profile: ScanProfile = ScanProfile.STANDARD
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    finding_count: int = 0

    model_config = ConfigDict(
        from_attributes=True,
    )


class ScanResultResponse(BaseModel):
    id: int
    port: int
    protocol: str
    state: str
    service: str | None
    product: str | None
    version: str | None
    is_ssl: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class ExecutorStatus(BaseModel):
    max_workers: int
    queued: int
    running: int
    idle_workers: int
    closed: bool


class ScanOperationsResponse(BaseModel):
    executor: ExecutorStatus
    counts: dict[str, int]
    total: int
