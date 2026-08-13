"""
In-memory publish/subscribe hub for scan lifecycle events.

Worker threads publish scan events; the WebSocket endpoint subscribes and
streams them to connected clients. The client keeps its polling fallback,
so the hub is an accelerator rather than a dependency.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any

_MAX_QUEUE_SIZE = 100


class ScanEventHub:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subscribers: dict[
            int,
            tuple[asyncio.Queue, set[str] | None],
        ] = {}
        self._next_id = 0
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """
        Bind the running server event loop so worker threads can dispatch
        events onto it safely.
        """

        self._loop = loop

    def subscribe(
        self,
        event_types: set[str] | None = None,
    ) -> tuple[int, asyncio.Queue]:
        """
        Register a new subscriber and return its id and event queue.

        ``event_types`` optionally restricts delivery to matching
        ``type`` values; ``None`` delivers every event.

        Must be called from the event-loop thread so the queue is created
        on the correct loop.
        """

        with self._lock:
            self._next_id += 1
            subscriber_id = self._next_id
            queue: asyncio.Queue = asyncio.Queue(
                maxsize=_MAX_QUEUE_SIZE,
            )
            self._subscribers[subscriber_id] = (
                queue,
                event_types,
            )
            return subscriber_id, queue

    def unsubscribe(self, subscriber_id: int) -> None:
        with self._lock:
            self._subscribers.pop(subscriber_id, None)

    def publish(self, event: dict[str, Any]) -> None:
        """
        Publish an event from any thread. Safe to call from scan workers.
        """

        loop = self._loop

        if loop is None:
            return

        loop.call_soon_threadsafe(self._deliver, event)

    def _deliver(self, event: dict[str, Any]) -> None:
        with self._lock:
            subscribers = list(self._subscribers.values())

        event_type = event.get("type")

        for queue, event_types in subscribers:
            if event_types is not None and event_type not in event_types:
                continue

            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass

            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

    @property
    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._subscribers)


scan_event_hub = ScanEventHub()
