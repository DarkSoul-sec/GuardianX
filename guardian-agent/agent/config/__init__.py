"""Agent configuration: schema, YAML loading and environment overrides."""

from __future__ import annotations

from agent.config.loader import (
    AgentConfig,
    CollectorConfig,
    load_config,
)

__all__ = ["AgentConfig", "CollectorConfig", "load_config"]