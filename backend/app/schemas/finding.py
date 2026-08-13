from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class FindingStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    ACCEPTED_RISK = "ACCEPTED_RISK"


class FindingListItem(BaseModel):
    id: int
    title: str
    severity: str
    cve: str | None = None
    cvss: float | None = None
    status: FindingStatus
    assigned_to: int | None = None
    assigned_to_name: str | None = None
    due_date: datetime | None = None
    created_at: datetime
    updated_at: datetime
    asset_name: str | None = None
    affected_service: str | None = None

    model_config = {
        "from_attributes": True,
    }


class FindingListResponse(BaseModel):
    items: list[FindingListItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    size: int = 20
    pages: int = 0


class FindingDetailResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    severity: str
    cve: str | None = None
    cvss: float | None = None
    affected_asset: str | None = None
    affected_service: str | None = None
    recommendation: str | None = None
    status: FindingStatus
    assigned_to: int | None = None
    assigned_to_name: str | None = None
    notes: str | None = None
    due_date: datetime | None = None
    created_at: datetime
    updated_at: datetime
    provider: str | None = None
    lookup_method: str | None = None
    confidence: str | None = None


class FindingIntelligenceResponse(BaseModel):
    """Asynchronous enrichment state for a CVE-backed finding."""

    status: Literal["not_available", "pending", "ready", "unavailable"]
    intelligence: dict | None = None


class FindingStatusUpdate(BaseModel):
    status: FindingStatus


class FindingTriageUpdate(BaseModel):
    status: FindingStatus | None = None
    assignee_id: int | None = None
    notes: str | None = None
    due_date: datetime | None = None


class FindingActivityResponse(BaseModel):
    id: int
    finding_id: int
    user_id: int | None = None
    username: str | None = None
    action: str
    old_value: str | None = None
    new_value: str | None = None
    created_at: datetime


class BulkFindingsStatusUpdate(BaseModel):
    ids: list[int] = Field(min_length=1, max_length=500)
    status: FindingStatus


class BulkUpdateResponse(BaseModel):
    updated: int
    ids: list[int] = Field(default_factory=list)


class FindingStatsResponse(BaseModel):
    total: int
    open: int
    in_progress: int
    resolved: int
    false_positive: int
    accepted_risk: int
    by_severity: dict[str, int] = Field(default_factory=dict)


class AssigneeResponse(BaseModel):
    id: int
    username: str
