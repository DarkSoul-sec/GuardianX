"""Loading and validation of ``agent.yaml``.

Configuration precedence (highest wins):

1. Environment variables prefixed ``GUARDIAN_AGENT_`` (``GUARDIAN_AGENT_SERVER_URL``).
2. Values from the YAML file.
3. Built-in defaults.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator

_KNOWN_COLLECTORS = (
    "process",
    "system_health",
    "logins",
    "services",
    "file_integrity",
    "usb",
    "startup",
)

_PREFIX = "GUARDIAN_AGENT_"


class CollectorConfig(BaseModel):
    """Per-collector toggles. Enabled set is controlled at the agent level."""

    enabled: bool = True
    interval_seconds: int = Field(default=300, ge=10)


class AgentConfig(BaseModel):
    """Complete validated agent configuration."""

    server_url: str = "http://127.0.0.1:8000/api"
    agent_name: str
    registration_token: str | None = None
    tls_verify: bool = True
    scan_interval: int = Field(default=60, ge=10)
    heartbeat_interval: int = Field(default=60, ge=10)
    enabled_collectors: list[str] = Field(
        default_factory=lambda: list(_KNOWN_COLLECTORS),
    )
    log_level: str = "INFO"
    log_format: str = "json"
    log_dir: str = "./logs"
    queue_path: str = "./data/agent-events.db"
    state_path: str = "./data/agent-state.json"
    connect_timeout: float = Field(default=5.0, gt=0)
    request_timeout: float = Field(default=15.0, gt=0)
    max_retries: int = Field(default=3, ge=0, le=10)
    batch_size: int = Field(default=50, ge=1, le=500)
    queue_high_water_bytes: int = Field(default=10_485_760, gt=0)
    collectors: dict[str, CollectorConfig] = Field(default_factory=dict)

    @field_validator("server_url")
    @classmethod
    def _strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")

    @field_validator("enabled_collectors")
    @classmethod
    def _validate_collectors(cls, value: list[str]) -> list[str]:
        unknown = [name for name in value if name not in _KNOWN_COLLECTORS]
        if unknown:
            raise ValueError(f"unknown collector(s): {', '.join(sorted(unknown))}")
        return list(dict.fromkeys(value))

    def collector_enabled(self, name: str) -> bool:
        if name not in _KNOWN_COLLECTORS:
            return False
        if name not in self.enabled_collectors:
            return False
        return self.collectors.get(name, CollectorConfig()).enabled

    def collector_interval(self, name: str) -> int:
        return self.collectors.get(name, CollectorConfig()).interval_seconds


def _env_override(key: str) -> str | None:
    env_name = _PREFIX + key.upper()
    return os.environ.get(env_name)


def _apply_env(raw: dict) -> dict:
    overrides = {
        "server_url": _env_override("server_url"),
        "agent_name": _env_override("agent_name"),
        "registration_token": _env_override("registration_token"),
        "tls_verify": _env_override("tls_verify"),
        "scan_interval": _env_override("scan_interval"),
        "heartbeat_interval": _env_override("heartbeat_interval"),
        "log_level": _env_override("log_level"),
        "log_format": _env_override("log_format"),
        "log_dir": _env_override("log_dir"),
        "queue_path": _env_override("queue_path"),
        "state_path": _env_override("state_path"),
    }
    for key, value in overrides.items():
        if value is not None:
            raw[key] = value
    return raw


def load_config(path: str | Path | None = None) -> AgentConfig:
    """Load configuration from ``agent.yaml`` (or ``path``) and env overrides."""
    raw: dict = {}

    file_path = Path(path) if path else Path("agent.yaml")
    if file_path.exists():
        loaded = yaml.safe_load(file_path.read_text())
        if isinstance(loaded, dict):
            raw = loaded

    raw = _apply_env(raw)
    return AgentConfig.model_validate(raw)