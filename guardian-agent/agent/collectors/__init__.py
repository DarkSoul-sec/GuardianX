"""Collector framework.

Each collector is an independent, read-only producer of observations. It never
mutates the system; it only inspects it and returns :class:`RawObservation`
instances that the scheduler normalizes into events.
"""

from __future__ import annotations

from agent.collectors.base import BaseCollector, Collector, CollectorError
from agent.collectors.registry import CollectorRegistry

__all__ = ["BaseCollector", "Collector", "CollectorError", "CollectorRegistry"]