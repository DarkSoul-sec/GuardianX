"""
Enterprise phishing detection module.

Analyzes a URL across URL structure, typosquatting, WHOIS age, SSL
certificate, DNS, VirusTotal reputation, public blacklists and suspicious
keywords, then produces a configurable threat score, risk level, reasons,
recommendations and an AI summary.

Reusable and config-driven: all detection lists, scoring weights and risk
thresholds come from the backend ``.env`` via :class:`PhishingConfig`, and the
analyzer set is pluggable through the analyzer registry.
"""

from __future__ import annotations

from app.detection.phishing.base import (
    Analyzer,
    CheckResult,
    UrlContext,
    build_url_context,
    clean_result,
)
from app.detection.phishing.config import PhishingConfig
from app.detection.phishing.schemas import (
    PhishingAnalysisRequest,
    PhishingAnalysisResponse,
    PhishingCheckResult,
)
from app.detection.phishing.service import analyze_url

__all__ = [
    "Analyzer",
    "CheckResult",
    "PhishingAnalysisRequest",
    "PhishingAnalysisResponse",
    "PhishingCheckResult",
    "PhishingConfig",
    "UrlContext",
    "analyze_url",
    "build_url_context",
    "clean_result",
]
