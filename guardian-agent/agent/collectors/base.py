"""Collector contracts and shared helpers.

Collectors are intentionally decoupled from the scheduler and the wire format:
they receive a wall-clock timestamp and return a list of
:class:`~agent.core.types.RawObservation` objects describing what they saw.

A base class provides two guards shared by every collector:

- **Read-only**: collectors must not perform side effects. The base class has
  no write helpers by design.
- **Deduplication**: snapshot-based collectors may re-discover the same
  condition across runs. The :class:`BaseCollector` exposes a LRU-style
  seen-set so a collector can report a condition only once (stopping duplicate
  telemetry without state files).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import OrderedDict
from datetime import datetime
from typing import Protocol

from agent.core.types import RawObservation


class CollectorError(Exception):
    """Raised when a collector cannot inspect a resource it must read."""


class Collector(Protocol):
    """Structural interface implemented by every collector."""

    name: str
    interval_seconds: int

    def collect(self, now: datetime) -> list[RawObservation]: ...


class BaseCollector(ABC):
    """Convenience base class with a bounded deduplication set."""

    interval_seconds: int

    def __init__(self, *, max_seen: int = 4096) -> None:
        self._seen: OrderedDict[str, bool] = OrderedDict()
        self._max_seen = max_seen

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable identifier used as the event ``source``."""

    @abstractmethod
    def collect(self, now: datetime) -> list[RawObservation]:
        """Inspect the system and return observations (or an empty list)."""

    def _seen(self, key: str) -> bool:
        """Return True if ``key`` was already observed, and record it."""
        seen = key in self._seen
        self._seen[key] = True
        self._seen.move_to_end(key)
        while len(self._seen) > self._max_seen:
            self._seen.popitem(last=False)
        return seen

    def _reset(self) -> None:
        self._seen.clear()