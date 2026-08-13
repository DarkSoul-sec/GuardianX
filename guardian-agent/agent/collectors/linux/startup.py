"""Startup items collector.

Enumerates the persistence mechanisms that would start a program at boot:
systemd unit files, cron jobs and XDG autostart ``.desktop`` files. Each item
is emitted once (deduplicated) so the dashboard can show the persistence
surface without telemetry spam.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from agent.collectors.base import BaseCollector
from agent.core.types import RawObservation

_SYSTEMD_DIRS = (
    "/etc/systemd/system",
    "/usr/lib/systemd/system",
    "/run/systemd/system",
)
_CRON_FILES = (
    "/etc/crontab",
    "/etc/cron.d",
    "/etc/cron.daily",
    "/etc/cron.hourly",
    "/etc/cron.weekly",
    "/etc/cron.monthly",
)
_AUTOSTART_DIRS = (
    "/etc/xdg/autostart",
)


class StartupCollector(BaseCollector):
    interval_seconds = 3600

    def __init__(self) -> None:
        super().__init__()
        self._home = Path.home() or Path("/root")

    @property
    def name(self) -> str:
        return "startup"

    def collect(self, now: datetime) -> list[RawObservation]:
        observations: list[RawObservation] = []

        for unit in self._systemd_units():
            item = {"kind": "systemd", "name": unit, "path": f"/etc/systemd/system/{unit}"}
            if not self._seen(f"startup:systemd:{unit}"):
                observations.append(RawObservation(event_type="startup_item", data=item))

        for crontab in self._cron_jobs():
            key = crontab["path"]
            if not self._seen(f"startup:cron:{key}"):
                observations.append(RawObservation(event_type="startup_item", data=crontab))

        for autostart in self._autostart():
            key = autostart["path"]
            if not self._seen(f"startup:autostart:{key}"):
                observations.append(RawObservation(event_type="startup_item", data=autostart))

        return observations

    def _systemd_units(self) -> list[str]:
        units: list[str] = []
        for directory in _SYSTEMD_DIRS:
            path = Path(directory)
            if not path.is_dir():
                continue
            try:
                units.extend(sorted(f.name for f in path.glob("*.service")))
            except OSError:
                continue
        return list(dict.fromkeys(units))

    def _cron_jobs(self) -> list[dict[str, Any]]:
        jobs: list[dict[str, Any]] = []
        for location in _CRON_FILES:
            path = Path(location)
            if path.is_file():
                jobs.append({"kind": "cron", "path": str(path), "name": f"File {path.name}"})
            elif path.is_dir():
                try:
                    for entry in sorted(path.iterdir()):
                        if entry.is_file():
                            jobs.append({"kind": "cron", "path": str(entry), "name": entry.name})
                except OSError:
                    continue
        return jobs

    def _autostart(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        dirs = list(_AUTOSTART_DIRS)
        user_autostart = self._home / ".config/autostart"
        if user_autostart.is_dir():
            dirs.append(str(user_autostart))
        for directory in dict.fromkeys(dirs):
            path = Path(directory)
            if not path.is_dir():
                continue
            try:
                for entry in sorted(path.glob("*.desktop")):
                    result.append({"kind": "autostart", "path": str(entry), "name": entry.name})
            except OSError:
                continue
        return result