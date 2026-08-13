from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ActivityResponse(BaseModel):
    id: int
    user_id: int
    action: str
    entity_type: str | None = None
    entity_id: int | None = None
    detail: str | None = None
    meta: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime


class ActivityListResponse(BaseModel):
    items: list[ActivityResponse] = Field(default_factory=list)
    total: int = 0