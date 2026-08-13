from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.copilot.intents import CopilotIntent


class CopilotChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    type: CopilotIntent | None = None
    asset_id: int | None = None
    finding_id: int | None = None
    cve: str | None = None


class CopilotResolvedContext(BaseModel):
    """
    Entities the Copilot actually analyzed, for display in the UI.
    """

    cve: str | None = None
    asset_id: int | None = None
    asset_name: str | None = None
    finding_id: int | None = None
    finding_title: str | None = None


class CopilotResultItem(BaseModel):
    """
    A single structured row returned by a natural-language search, ready for
    the UI to render as a table or card.
    """

    kind: Literal["finding", "asset", "service", "cve"]
    id: int | None = None
    title: str
    detail: str | None = None
    severity: str | None = None
    status: str | None = None
    score: str | None = None


class CopilotChatResponse(BaseModel):
    answer: str
    intent: CopilotIntent
    provider: str
    model: str | None = None
    context: CopilotResolvedContext | None = None
    results: list[CopilotResultItem] | None = None


class CopilotProviderInfo(BaseModel):
    provider: str
    model: str | None = None
    built_in: bool = False
    available: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class CopilotMemoryStatus(BaseModel):
    turns: int = 0
    ttl_seconds: int = 0


class CopilotMemoryClearResponse(BaseModel):
    cleared: int = 0
