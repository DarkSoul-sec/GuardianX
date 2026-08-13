"""
Threat Intelligence platform schemas.

These are the normalized contracts returned by the ``app.intelligence`` API.
Raw VirusTotal payloads never cross the API boundary — every field is derived
in ``providers.virustotal`` and validated against these models before leaving
the service layer.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class IOCType(str, Enum):
    """The automatically detected kind of indicator of compromise."""

    IP = "ip"
    DOMAIN = "domain"
    URL = "url"
    HASH = "hash"


class ThreatLevel(str, Enum):
    """Risk-tier assigned to a scanned indicator."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CLEAN = "clean"
    UNKNOWN = "unknown"


class LookupRequest(BaseModel):
    """An IP address, domain, URL or SHA256 hash to analyze."""

    value: str = Field(min_length=1, max_length=2048)


class VendorDetectionEntry(BaseModel):
    """A single antivirus engine verdict for the analyzed indicator."""

    engine: str
    category: str
    result: str | None = None
    engine_version: str | None = None
    update_date: datetime | None = None


class CommunityVotes(BaseModel):
    """Community reputation votes collected by the provider."""

    malicious: int = 0
    harmless: int = 0


class MitreMapping(BaseModel):
    """A MITRE ATT&CK technique inferred from the indicator's behavior."""

    tactic: str
    technique_id: str
    technique: str
    description: str | None = None


class ThreatIntelligenceReport(BaseModel):
    """The full GuardianX intelligence dashboard for a single IOC."""

    resource_type: IOCType
    resource: str
    permalink: str
    found: bool = False
    detected: bool = False
    threat_level: ThreatLevel = ThreatLevel.UNKNOWN
    risk_score: int = 0
    reputation: int = 0
    community_score: int = 0
    detection_ratio: str = "0/0"
    threat_category: str | None = None
    last_analysis: datetime | None = None
    country: str | None = None
    asn: str | None = None
    as_owner: str | None = None
    registrar: str | None = None
    creation_date: datetime | None = None
    first_seen: datetime | None = None
    first_submission: datetime | None = None
    last_submission: datetime | None = None
    submission_count: int = 0
    community_votes: CommunityVotes = Field(default_factory=CommunityVotes)
    malicious: int = 0
    suspicious: int = 0
    harmless: int = 0
    undetected: int = 0
    total: int = 0
    categories: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    mitre: list[MitreMapping] = Field(default_factory=list)
    vendor_detections: list[VendorDetectionEntry] = Field(default_factory=list)
    from_cache: bool = False


class IntelligenceLookupResponse(BaseModel):
    """Outcome of an IOC lookup, including the persisted history id."""

    report: ThreatIntelligenceReport
    history_id: int | None = None


class IntelligenceHistoryItem(BaseModel):
    """A compact summary of a previously executed IOC search."""

    id: int
    resource_type: IOCType
    resource: str
    threat_level: ThreatLevel
    risk_score: int
    reputation: int
    detected: bool
    malicious: int
    suspicious: int
    harmless: int
    undetected: int
    detection_ratio: str
    threat_category: str | None
    created_at: datetime


class IntelligenceHistoryResponse(BaseModel):
    """A page of search history entries."""

    items: list[IntelligenceHistoryItem]
    total: int
    page: int
    limit: int


class IntelligenceStatus(BaseModel):
    """Whether the Threat Intelligence provider is configured."""

    provider: str = "virustotal"
    configured: bool = False


class DeleteHistoryResponse(BaseModel):
    """Outcome of removing one or more history entries."""

    deleted: bool = False
