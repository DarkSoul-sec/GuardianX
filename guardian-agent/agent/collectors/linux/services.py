"""Service collector.

Reads the list of systemd service units plus their state, and also records
state transitions (started/stopped/restarted/failed) by diffing successive
runs with the agent's deduplication set.

Read-only: only calls ``systemctl`` with fixed, non-shell argument vectors.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from agent.collectors.base import BaseCollector
from agent.collectors.linux.commands import CommandError, run_capture
from agent.core.types import RawObservation


class ServiceCollector(BaseCollector):
    interval_seconds = 180

    @property
    def name(self) -> str:
        return "services"

    def collect(self, now: datetime) -> list[RawObservation]:
        units = self._list_units()
        if not units:
            return []

        observations: list[RawObservation] = []
        state_map: dict[str, str] = {}

        for unit in units:
            name, load, active, sub = unit
            state_map[name] = sub or active or "unknown"
            observations.append(
                RawObservation(
                    event_type="service_snapshot",
                    data={"unit": name, "load": load, "active": active, "state": sub or "", "timestamp": now.isoformat()},
                )
            )

        # Report only meaningful state transitions once per unit-state pair.
        for name, state in state_map.items():
            marker = f"transition:{name}:{state}"
            if not self._seen(marker):
                observations.append(
                    RawObservation(
                        event_type="service_state",
                        severity=("warning" if state in {"failed", "inactive"} else "info"),
                        data={"unit": name, "state": state, "timestamp": now.isoformat()},
                    )
                )

        return observations

    def _list_units(self) -> list[tuple[str, str, str, str]]:
        try:
            raw = run_capture(
                ["systemctl", "list-units", "--type=service", "--all", "--no-pager", "--no-legend", "--plain"],
                timeout=8.0,
            )
        except CommandError:
            return []
        units: list[tuple[str, str, str, str]] = []
        for line in raw.splitlines():
            parts = line.split()
            # systemctl columns: UNIT LOAD ACTIVE SUB DESCRIPTION
            if len(parts) < 4:
                continue
            units.append((parts[0], parts[1], parts[2], parts[3]))
        return units