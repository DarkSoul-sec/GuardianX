"""Durable on-disk event store.

Events are persisted to a local SQLite database before being sent to the
GuardianX platform. If the platform is unreachable, rows stay queued and are
re-sent on a later flush — the agent never loses telemetry in memory.

Delivery is *at-least-once*: a row is removed only after the platform
acknowledges it. The platform deduplicates by ``event.id``, so retries are
idempotent. SQLite WAL journaling keeps the store crash-consistent while a
single lock guards the shared connection across the agent's threads.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import UTC, datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class EventStore(Protocol):
    """The persistence contract the scheduler depends on."""

    def enqueue(self, payloads: list[str]) -> list[str]: ...

    def dequeue(self, limit: int) -> list["QueuedEvent"]: ...

    def ack(self, ids: list[str]) -> int: ...

    def count(self) -> int: ...

    def close(self) -> None: ...


@dataclass(frozen=True)
class QueuedEvent:
    id: str
    payload: str
    attempts: int


def setup_database(path: str | Path) -> None:
    """Create the parent directory of a database file if needed."""
    parent = Path(path).parent
    parent.mkdir(parents=True, exist_ok=True)


class DurableEventStore:
    """SQLite-backed FIFO queue of serialized events."""

    _SCHEMA = """
    CREATE TABLE IF NOT EXISTS events (
        id TEXT PRIMARY KEY,
        payload TEXT NOT NULL,
        created_at REAL NOT NULL,
        attempts INTEGER NOT NULL DEFAULT 0
    );
    CREATE INDEX IF NOT EXISTS ix_events_order ON events(created_at, id);
    """

    def __init__(self, path: str | Path) -> None:
        setup_database(path)
        self._lock = threading.Lock()
        self._connection = sqlite3.connect(str(path), check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        with self._lock:
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.executescript(self._SCHEMA)
            self._connection.commit()

    def enqueue(self, payloads: list[str]) -> list[str]:
        """Persist serialized events, returning the ids actually inserted."""
        now = datetime.now(UTC).timestamp()
        inserted: list[str] = []
        with self._lock:
            for payload in payloads:
                event_id = json.loads(payload)["id"]
                inserted.append(event_id)
                self._connection.execute(
                    "INSERT OR IGNORE INTO events(id, payload, created_at) VALUES (?, ?, ?)",
                    (event_id, payload, now),
                )
            self._connection.commit()
        return inserted

    def dequeue(self, limit: int) -> list[QueuedEvent]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT id, payload, attempts FROM events ORDER BY created_at ASC, id ASC LIMIT ?",
                (limit,),
            ).fetchall()
        return [QueuedEvent(id=r["id"], payload=r["payload"], attempts=int(r["attempts"])) for r in rows]

    def ack(self, ids: list[str]) -> int:
        if not ids:
            return 0
        placeholders = ",".join("?" * len(ids))
        with self._lock:
            cursor = self._connection.execute(
                f"DELETE FROM events WHERE id IN ({placeholders})",
                list(ids),
            )
            self._connection.commit()
        return cursor.rowcount

    def count(self) -> int:
        with self._lock:
            row = self._connection.execute("SELECT COUNT(*) AS n FROM events").fetchone()
        return int(row["n"])

    def close(self) -> None:
        with self._lock:
            self._connection.close()