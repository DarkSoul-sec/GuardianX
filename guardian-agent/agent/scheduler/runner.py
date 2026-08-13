"""The agent runtime loop.

:class:`AgentRunner` owns three cooperating threads:

- **collector**: runs each enabled collector on its own interval (skipping a
  collector that is still busy), normalizes its observations and queues them
  to the durable store.
- **heartbeat**: sends a :class:`~agent.core.types.Heartbeat` on the heartbeat
  interval.
- **flusher**: drains queued events and pushes them to the platform in
  batches. On failure every event stays queued, so nothing is lost.

Every task cooperates on a shared stop event for clean shutdown.
"""

from __future__ import annotations

import json
import threading
from typing import Any

from agent.collectors.registry import CollectorRegistry
from agent.communication.client import ApiClient, GuardianError
from agent.config.loader import AgentConfig
from agent.core.clock import Clock
from agent.core.normalizer import Normalizer
from agent.core.types import Heartbeat
from agent.database.queue import DurableEventStore
from agent.logging.structured import get_logger
from agent.security.manager import CredentialManager

log = get_logger("agent.scheduler")


class PeriodicTask(threading.Thread):
    """Repeatedly runs ``func`` until the shared stop event fires."""

    def __init__(
        self,
        name: str,
        func: Any,
        stop_event: threading.Event,
        interval: float = 60.0,
    ) -> None:
        super().__init__(name=name, daemon=True)
        self._func = func
        self._stop = stop_event
        self._interval = interval

    def run(self) -> None:
        while not self._stop.wait(self._interval):
            try:
                self._func()
            except Exception:
                log.exception("task %s failed", self.name)


class AgentRunner:
    """Composes collectors, queue, client and credentials into a running agent."""

    def __init__(
        self,
        config: AgentConfig,
        registry: CollectorRegistry,
        queue: DurableEventStore,
        client: ApiClient,
        credentials: CredentialManager,
        clock: Clock,
        normalizer: Normalizer,
    ) -> None:
        self._config = config
        self._registry = registry
        self._queue = queue
        self._client = client
        self._credentials = credentials
        self._clock = clock
        self._normalizer = normalizer
        self._stop = threading.Event()
        self._last_run: dict[str, float] = {}
        self._collector_status: dict[str, str] = {}

    @property
    def registered(self) -> bool:
        return self._credentials.agent_id is not None

    def run(self) -> None:
        """Register (if needed) then start all background tasks."""
        if not self.registered:
            self._credentials.ensure_registered()
            log.info("agent registered as %s", self._credentials.agent_id)
        if self._credentials.agent_id:
            self._normalizer.agent_id = self._credentials.agent_id

        threads = [
            PeriodicTask("collector", self._collect_pass, self._stop, 1.0),
            PeriodicTask(
                "heartbeat",
                self._send_heartbeat,
                self._stop,
                float(self._config.heartbeat_interval),
            ),
            PeriodicTask("flusher", self._flush, self._stop, 5.0),
        ]
        for thread in threads:
            thread.start()

        log.info("guardian-agent started")

    def stop(self) -> None:
        self._stop.set()
        log.info("guardian-agent stopping")

    # -- internal tasks -------------------------------------------------------
    def _collect_pass(self) -> None:
        now = self._clock.now()
        mono = self._clock.monotonic()
        for name in self._registry.names():
            collector = self._registry.get(name)
            if collector is None:
                continue
            interval = float(getattr(collector, "interval_seconds", self._config.scan_interval))
            if not self._due(name, mono, interval):
                continue
            observations = self._registry.collect(name, now)
            self._collector_status[name] = "ok" if observations else "empty"
            if not observations:
                continue
            events = self._normalizer.normalize(name, observations, now)
            payloads = [event.model_dump(mode="json") for event in events]
            self._queue.enqueue(payloads)
            log.info("collected %s observations from %s", len(observations), name)

    def _due(self, name: str, mono: float, interval: float) -> bool:
        last = self._last_run.get(name)
        if last is None:
            self._last_run[name] = mono
            return True
        if mono - last >= interval:
            self._last_run[name] = mono
            return True
        return False

    def _send_heartbeat(self) -> None:
        try:
            from agent.collectors.linux import system as system_info
        except ImportError:
            return
        rx, tx = system_info.network_bytes()
        metrics = Heartbeat(
            agent_id=self._credentials.agent_id or "",
            agent_name=self._config.agent_name,
            version=_agent_version(),
            hostname=system_info.hostname(),
            os=system_info.os_name(),
            kernel_version=system_info.kernel_version(),
            uptime_seconds=system_info.system_uptime_seconds(self._clock.now()),
            cpu_percent=system_info.cpu_percent(),
            ram_total_bytes=system_info.ram_total_bytes(),
            ram_used_bytes=system_info.ram_used_bytes(),
            disk_used_percent=system_info.disk_used_percent("/"),
            network_rx_bytes=rx,
            network_tx_bytes=tx,
            health_score=100.0,
            collector_status=dict(self._collector_status),
            timestamp=self._clock.now(),
        )
        try:
            self._client.send_heartbeat(metrics.model_dump(mode="json"))
        except GuardianError:
            log.debug("heartbeat could not reach platform")
        except Exception:
            log.exception("heartbeat failed")

    def _flush(self) -> None:
        batch = self._queue.dequeue(self._config.batch_size)
        if not batch:
            return
        events = [json.loads(item.payload) for item in batch]
        try:
            acked = self._client.send_events(events)
        except GuardianError:
            log.warning(
                "event delivery failed; %s events remain queued",
                self._queue.count(),
            )
            return
        except Exception:
            log.exception("event flush failed")
            return
        self._queue.ack([item.id for item in batch[:acked]])


def _agent_version() -> str:
    from agent import __version__

    return __version__