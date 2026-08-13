"""
Client-side rate limiting for outbound API traffic.

A thread-safe token bucket throttles calls to the VirusTotal API so a burst
of lookups cannot exceed the configured per-minute budget. When the bucket is
empty, ``acquire`` blocks the calling thread until a token refills.
"""

from __future__ import annotations

import threading
import time


class TokenBucket:
    """A minimal thread-safe token bucket."""

    def __init__(self, capacity: float, refill_per_second: float) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be greater than zero")
        if refill_per_second <= 0:
            raise ValueError("refill_per_second must be greater than zero")

        self._capacity = float(capacity)
        self._refill_per_second = float(refill_per_second)
        self._tokens = self._capacity
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(
            self._capacity,
            self._tokens + elapsed * self._refill_per_second,
        )
        self._last_refill = now

    def acquire(self) -> None:
        """Block until a token is available, then consume it."""
        while True:
            with self._lock:
                self._refill()

                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return

                wait = (1.0 - self._tokens) / self._refill_per_second

            time.sleep(max(wait, 0.05))
