"""Process collector.

Reports a snapshot of every visible process with its identity, resource usage
and start time. Read-only; uses the ``psutil`` process table. Average CPU is
derived from cumulative process CPU seconds over elapsed runtime, so it is a
stable value instead of a volatile instant sample.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import psutil

from agent.collectors.base import BaseCollector
from agent.core.types import RawObservation


class ProcessCollector(BaseCollector):
    interval_seconds = 60

    @property
    def name(self) -> str:
        return "process"

    def collect(self, now: datetime) -> list[RawObservation]:
        rows: list[RawObservation] = []
        seen: set[int] = set()

        for proc in psutil.process_iter(["pid", "ppid", "name", "exe"]):
            try:
                info: dict[str, Any] = {
                    "pid": proc.info["pid"],
                    "name": proc.info["name"],
                    "parent_pid": proc.info["ppid"],
                    "exe": proc.info["exe"] or None,
                    "command_line": _safe_cmdline(proc),
                    "username": _safe_user(proc),
                    "cpu_percent": _avg_cpu_percent(proc, now),
                    "memory_bytes": _safe_memory(proc),
                    "start_time": _safe_create_time(proc),
                }
                pid = int(info["pid"])
                if pid in seen:
                    continue
                seen.add(pid)
                rows.append(
                    RawObservation(event_type="process_snapshot", data=info)
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception:
                continue

        return rows


def _safe_cmdline(proc: psutil.Process) -> str:
    try:
        return " ".join(proc.cmdline())[:2048]
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return ""


def _safe_user(proc: psutil.Process) -> str | None:
    try:
        return proc.username()
    except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
        return None


def _avg_cpu_percent(proc: psutil.Process, now: datetime) -> float:
    try:
        times = proc.cpu_times()
        cpu_seconds = times.user + times.system
        created = datetime.fromtimestamp(proc.create_time(), tz=now.tzinfo)
        elapsed = max((now - created).total_seconds(), 1.0)
        return round(100.0 * cpu_seconds / elapsed, 2)
    except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
        return 0.0


def _safe_memory(proc: psutil.Process) -> int:
    try:
        return int(proc.memory_info().rss)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return 0


def _safe_create_time(proc: psutil.Process) -> str | None:
    try:
        return datetime.fromtimestamp(proc.create_time(), tz=datetime.now().astimezone().tzinfo).isoformat()
    except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
        return None