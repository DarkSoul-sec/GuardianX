"""
Bounded, dependency-free scan executor.

Scans are queued and executed by a small pool of daemon worker threads so
that an arbitrary number of scan requests can be accepted without unbounded
thread growth or blocking the API request cycle. Concurrency is limited by
`settings.SCAN_MAX_WORKERS`.
"""

from __future__ import annotations

import queue
import threading

from app.core.config import settings
from app.logger import logger


def _default_handler(scan_id: int) -> None:
    """
    Default worker callback.

    Imported lazily to avoid a circular import between this module and the
    scan service.
    """

    from app.services.scan_service import run_scan_in_background

    run_scan_in_background(scan_id)


class ScanExecutor:
    """
    Execute scan jobs on a bounded pool of daemon worker threads.
    """

    def __init__(
        self,
        max_workers: int,
        handler,
    ) -> None:
        self._max_workers = max(1, max_workers)
        self._handler = handler
        self._queue: "queue.Queue[int]" = queue.Queue()
        self._closed = False
        self._running = 0
        self._lock = threading.Lock()
        self._workers: list[threading.Thread] = []

        self._spawn_workers()

    def _spawn_workers(self) -> None:
        for index in range(self._max_workers):
            worker = threading.Thread(
                target=self._run_loop,
                name=f"scan-worker-{index}",
                daemon=True,
            )
            worker.start()
            self._workers.append(worker)

    def _run_loop(self) -> None:
        while True:
            try:
                scan_id = self._queue.get(timeout=1)
            except queue.Empty:
                if self._closed and self._queue.empty():
                    return
                continue

            with self._lock:
                self._running += 1

            try:
                self._handler(scan_id)
            except Exception:
                logger.exception(
                    "Scan worker failed for scan %s.",
                    scan_id,
                )
            finally:
                with self._lock:
                    self._running -= 1
                self._queue.task_done()

    def submit(self, scan_id: int) -> bool:
        """
        Queue a scan for execution.

        Returns False when the executor is already shutting down and the
        scan was not queued.
        """

        with self._lock:
            if self._closed:
                logger.warning(
                    "Scan %s not queued: executor is shutting down.",
                    scan_id,
                )
                return False

            self._queue.put(scan_id)

        logger.debug(
            "Scan %s queued for execution.",
            scan_id,
        )

        return True

    @property
    def queued(self) -> int:
        """Number of scans waiting to be picked up."""
        return self._queue.qsize()

    @property
    def running(self) -> int:
        """Number of scans currently being executed."""
        with self._lock:
            return self._running

    @property
    def max_workers(self) -> int:
        return self._max_workers

    @property
    def closed(self) -> bool:
        with self._lock:
            return self._closed

    def status(self) -> dict:
        """
        Snapshot of the executor for observability and the operations API.
        """

        with self._lock:
            return {
                "max_workers": self._max_workers,
                "queued": self._queue.qsize(),
                "running": self._running,
                "idle_workers": max(
                    0,
                    self._max_workers - self._running,
                ),
                "closed": self._closed,
            }

    def shutdown(self) -> None:
        """
        Stop accepting new scans and let queued work drain.

        Worker threads are daemons, so a running scan will never block
        interpreter exit.
        """

        with self._lock:
            if self._closed:
                return

            self._closed = True

        logger.info(
            "Scan executor shutting down (%d queued).",
            self.queued,
        )


scan_executor = ScanExecutor(
    max_workers=settings.SCAN_MAX_WORKERS,
    handler=_default_handler,
)
