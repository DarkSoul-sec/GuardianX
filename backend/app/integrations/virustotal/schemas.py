"""
Normalized VirusTotal schemas returned by the GuardianX API routes.

Both the connection/management flow and the intelligence lookups use these
schemas — raw VirusTotal payloads never cross the API boundary.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class VendorDetection(BaseModel):
    """A single vendor engine verdict for the analyzed resource."""

    engine: str
    category: str
    result: str | None = None


class VirusTotalLookupResponse(BaseModel):
    """Normalized reputation report for a URL, domain, IP or file hash."""

    resource_type: str
    resource: str
    permalink: str
    found: bool = False
    detected: bool = False
    malicious: int = 0
    suspicious: int = 0
    undetected: int = 0
    harmless: int = 0
    timeout: int = 0
    total: int = 0
    detection_ratio: str = "0/0"
    reputation: int = 0
    community_score: int = 0
    threat_category: str | None = None
    last_analysis_date: datetime | None = None
    vendor_detections: list[VendorDetection] = Field(default_factory=list)


class VirusTotalConnectionStatus(BaseModel):
    """Result of an immediate key-validation call to VirusTotal."""

    status: str
    message: str


class IntegrationStatus(BaseModel):
    """Persisted connection state for a user's VirusTotal integration."""

    provider: str = "virustotal"
    configured: bool = False
    status: str = "not_configured"
    message: str = "Add your VirusTotal API key to get started."
    last_tested_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ConnectRequest(BaseModel):
    """A VirusTotal API key to validate, encrypt and store."""

    api_key: str = Field(min_length=32, max_length=200)


class TestConnectionRequest(BaseModel):
    """Optionally validate a candidate key without saving it."""

    api_key: str | None = Field(default=None, min_length=32, max_length=200)


class ConnectResponse(BaseModel):
    """Outcome of saving a VirusTotal API key."""

    status: IntegrationStatus


class TestConnectionResponse(BaseModel):
    """Outcome of validating a VirusTotal API key."""

    status: IntegrationStatus


class DisconnectResponse(BaseModel):
    """Outcome of removing a VirusTotal API key."""

    disconnected: bool = False


class IntelligenceRequest(BaseModel):
    """A URL, domain, IP address or SHA256 hash to look up."""

    value: str = Field(min_length=1, max_length=2000)
