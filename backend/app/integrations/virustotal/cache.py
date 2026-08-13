"""
Thread-safe in-process TTL cache.

Values are stored alongside a monotonic expiry timestamp. ``None`` is a
valid cached value, but this cache is always written with fully-formed
response objects, so a ``get`` that returns ``None`` unambiguously means
"cache miss" (see ``app.integrations.virustotal.service``).
"""

from __future__ import annotations

import threading
import time
from typing import Generic, TypeVar

T = TypeVar("T")


class TTLCache(Generic[T]):
    """Simple bounded TTL cache guarded by a lock."""

    def __init__(self, ttl_seconds: int, max_entries: int) -> None:
        self._ttl_seconds = ttl_seconds
        self._max_entries = max_entries
        self._lock = threading.Lock()
        self._store: dict[str, tuple[float, T]] = {}

    def get(self, key: str) -> T | None:
        with self._lock:
            entry = self._store.get(key)

        if entry is None:
            return None

        expires_at, value = entry

        if time.monotonic() > expires_at:
            with self._lock:
                self._store.pop(key, None)
            return None

        return value

    def set(self, key: str, value: T) -> None:
        with self._lock:
            if len(self._store) >= self._max_entries and key not in self._store:
                self._store.clear()

            self._store[key] = (time.monotonic() + self._ttl_seconds, value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
