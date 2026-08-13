"""Thread-safe in-process TTL cache shared by the threat intel clients."""

from __future__ import annotations

import threading
import time

from typing import Any


class TTLCache:
    """Simple monotonic-clock cache with a hard entry cap."""

    def __init__(
        self,
        ttl_seconds: int = 1800,
        max_entries: int = 512,
    ) -> None:
        self._ttl = ttl_seconds
        self._max = max_entries
        self._lock = threading.Lock()
        self._data: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._data.get(key)

        if entry is None:
            return None

        expires_at, value = entry

        if time.monotonic() > expires_at:
            return None

        return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            if len(self._data) >= self._max and key not in self._data:
                self._data.clear()
            self._data[key] = (time.monotonic() + self._ttl, value)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()
