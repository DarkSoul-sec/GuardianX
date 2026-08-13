"""
API schemas for phishing analysis.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PhishingAnalysisRequest(BaseModel):
    """Body for the phishing analyze endpoint."""

    url: str


class PhishingCheckResult(BaseModel):
    """Normalized result of a single phishing check."""

    check: str
    title: str
    score: int
    severity: str
    reason: str
    recommendation: str = ""
    data: dict[str, Any] = Field(default_factory=dict)


class PhishingAnalysisResponse(BaseModel):
    """Full phishing analysis verdict for a URL."""

    url: str
    threat_score: int
    risk_level: str
    reasons: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    ai_summary: str = ""
    checks: list[PhishingCheckResult] = Field(default_factory=list)
    generated_at: datetime
