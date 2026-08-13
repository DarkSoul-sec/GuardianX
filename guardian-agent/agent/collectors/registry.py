"""Collector registry.

The registry maps collector names to their instances and exposes a single
``collect()`` entry point used by the scheduler. Registering an additional
collector is a one-line call, so future platforms (Windows, macOS) and future
collectors (Sysmon, Docker, Kubernetes) slot in without touching the scheduler.
"""

from __future__ import annotations

from datetime import datetime

from agent.collectors.base import Collector, CollectorError
from agent.config.loader import AgentConfig
from agent.core.types import RawObservation


class CollectorRegistry:
    """Holds enabled collectors keyed by name."""

    def __init__(self) -> None:
        self._collectors: dict[str, Collector] = {}

    def register(self, collector: Collector) -> None:
        if collector.name in self._collectors:
            raise ValueError(f"collector '{collector.name}' is already registered")
        self._collectors[collector.name] = collector

    def get(self, name: str) -> Collector | None:
        return self._collectors.get(name)

    def names(self) -> list[str]:
        return list(self._collectors)

    def collect(self, name: str, now: datetime) -> list[RawObservation]:
        """Collect observations for one collector, swallowing read errors."""
        collector = self._collectors.get(name)
        if collector is None:
            return []
        try:
            return collector.collect(now)
        except CollectorError:
            # A transient read failure on a single collector must never stop
            # the agent; the failure is recorded as an empty result and the
            # heartbeat independently reports per-collector status.
            return []
        except Exception:
            return []

    @classmethod
    def from_config(
        cls,
        config: AgentConfig,
        linux_collectors: dict[str, Collector],
    ) -> "CollectorRegistry":
        """Build a registry honouring the enabled set in ``config``."""
        registry = cls()
        for name, collector in linux_collectors.items():
            if config.collector_enabled(name):
                registry.register(collector)
        return registry