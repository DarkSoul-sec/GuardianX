"""
Raw VirusTotal v3 response models.

These mirror the ``data.attributes`` shape returned by the
``/urls``, ``/domains``, ``/ip_addresses`` and ``/files`` endpoints. Extra
fields are intentionally ignored so the models stay resilient to additive
API changes.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AnalysisStats(BaseModel):
    """Vendor verdict counts from ``last_analysis_stats``."""

    malicious: int = 0
    suspicious: int = 0
    undetected: int = 0
    harmless: int = 0
    timeout: int = 0
    confirmed_timeout: int = 0
    failure: int = 0
    type_unsupported: int = 0


class VendorResult(BaseModel):
    """Per-engine verdict from ``last_analysis_results``."""

    engine_name: str = ""
    category: str = ""
    result: str | None = None


class Attributes(BaseModel):
    """The ``data.attributes`` object of a VirusTotal report."""

    last_analysis_stats: AnalysisStats | None = None
    last_analysis_results: dict[str, VendorResult] = Field(default_factory=dict)
    last_analysis_date: int | None = None
    reputation: int | None = None
    meaningful_name: str | None = None
    type_description: str | None = None
    popular_threat_category: str | None = None
    categories: dict[str, str] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class Data(BaseModel):
    """The ``data`` object of a VirusTotal report."""

    id: str
    type: str
    attributes: Attributes


class RawReport(BaseModel):
    """Top-level VirusTotal v3 response envelope."""

    data: Data
