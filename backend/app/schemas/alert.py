from datetime import datetime

from pydantic import BaseModel, Field


class AlertResponse(BaseModel):
    id: int
    user_id: int
    alert_type: str
    title: str
    body: str | None = None
    severity: str
    source: str
    finding_id: int | None = None
    asset_id: int | None = None
    status: str
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    created_at: datetime


class AlertListResponse(BaseModel):
    items: list[AlertResponse] = Field(default_factory=list)
    total: int = 0
    open: int = 0


class AlertStatusUpdate(BaseModel):
    status: str


class IncidentCreate(BaseModel):
    title: str
    description: str | None = None
    severity: str = "MEDIUM"
    status: str = "OPEN"
    asset_id: int | None = None
    alert_id: int | None = None
    finding_id: int | None = None
    assignee_id: int | None = None


class IncidentUpdate(BaseModel):
    status: str | None = None
    assignee_id: int | None = None
    summary: str | None = None


class IncidentResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: str | None = None
    severity: str
    status: str
    asset_id: int | None = None
    alert_id: int | None = None
    finding_id: int | None = None
    assignee_id: int | None = None
    summary: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class IncidentListResponse(BaseModel):
    items: list[IncidentResponse] = Field(default_factory=list)
    total: int = 0
    open: int = 0


class AlertSummaryResponse(BaseModel):
    open: int = 0
    acknowledged: int = 0
    critical: int = 0