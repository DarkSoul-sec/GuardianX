from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SessionResponse(BaseModel):
    id: int
    created_at: datetime
    expires_at: datetime
    user_agent: str | None
    ip_address: str | None

    model_config = ConfigDict(from_attributes=True)


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]