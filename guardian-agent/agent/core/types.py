"""Typed payloads exchanged between the agent and the GuardianX platform.

These classes are deliberately small and dependency-free (pydantic only) so
collector output, the local queue, and the outbound HTTP client all speak the
same shape.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EndpointEvent(BaseModel):
    """A single normalized telemetry event produced by a collector."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    agent_id: str
    source: str
    event_type: str
    timestamp: datetime
    severity: str = Field(default="info", pattern="^(info|warning|critical)$")
    data: dict[str, Any] = Field(default_factory=dict)


class RawObservation(BaseModel):
    """Raw output of a collector before normalization.

    Collectors return *observations* describing what they saw; the normalizer
    turns each observation into an :class:`EndpointEvent`.
    """

    event_type: str
    severity: str = "info"
    data: dict[str, Any] = Field(default_factory=dict)


class Heartbeat(BaseModel):
    """Health and metrics snapshot sent to the platform every heartbeat."""

    agent_id: str
    agent_name: str
    version: str
    hostname: str
    os: str
    kernel_version: str
    uptime_seconds: float
    cpu_percent: float
    ram_total_bytes: int
    ram_used_bytes: int
    disk_used_percent: float
    network_rx_bytes: int
    network_tx_bytes: int
    health_score: float
    collector_status: dict[str, str] = Field(default_factory=dict)
    timestamp: datetime


class AgentTokens(BaseModel):
    """Credentials used to authenticate every request to GuardianX."""

    agent_id: str
    access_token: str
    refresh_token: str
    expires_at: datetime