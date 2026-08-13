"""Time source abstraction.

A clock is injected everywhere a collector or task needs ``now`` or a
monotonic timestamp. Tests substitute a :class:`FakeClock` to make every
interval and timestamp deterministic without touching real time.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    """Provides wall-clock and monotonic time for the agent."""

    def now(self) -> datetime:
        """Return the current UTC wall-clock time."""

    def monotonic(self) -> float:
        """Return a monotonically increasing seconds counter."""


class SystemClock:
    """The default clock backed by the operating system."""

    def now(self) -> datetime:
        return datetime.now(UTC)

    def monotonic(self) -> float:
        return time.monotonic()


class FakeClock:
    """Deterministic clock for tests; time advances only when told to."""

    def __init__(self, start: datetime | None = None) -> None:
        from datetime import timedelta

        self._now = start or datetime(2026, 1, 1, tzinfo=UTC)
        self._mono = 0.0
        self._step = timedelta(seconds=1)

    def now(self) -> datetime:
        return self._now

    def monotonic(self) -> float:
        return self._mono

    def advance(self, seconds: float) -> None:
        """Advance both wall-clock and monotonic time by ``seconds``."""
        from datetime import timedelta

        self._now = self._now + timedelta(seconds=seconds)
        self._mono += seconds