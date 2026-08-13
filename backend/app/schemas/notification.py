from datetime import datetime

from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    notification_type: str
    title: str
    body: str | None = None
    severity: str | None = None
    finding_id: int | None = None
    read_at: datetime | None = None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse] = Field(default_factory=list)
    total: int = 0
    unread: int = 0


class UnreadCountResponse(BaseModel):
    unread: int
