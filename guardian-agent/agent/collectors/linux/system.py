"""Shared, read-only system metric helpers.

Every function here is a pure snapshot reader (``/proc``, ``psutil``, kernel
API). None of them mutate the system; the agent is strictly observational.
Functions degrade gracefully to safe defaults so a privileged path that is
unreadable never raises.
"""

from __future__ import annotations

import os
import platform
import shutil
import socket
from datetime import UTC, datetime, timedelta

import psutil


def hostname() -> str:
    return socket.gethostname()


def kernel_version() -> str:
    return platform.release()


def os_name() -> str:
    distro = "/etc/os-release"
    try:
        with open(distro, encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return f"Linux ({kernel_version()})"


def cpu_percent() -> float:
    try:
        return float(psutil.cpu_percent(interval=None))
    except Exception:  # pragma: no cover - defensive
        return 0.0


def load_average() -> tuple[float, float, float]:
    try:
        return os.getloadavg()
    except OSError:  # pragma: no cover - not available on every platform
        return (0.0, 0.0, 0.0)


def ram_total_bytes() -> int:
    try:
        return int(psutil.virtual_memory().total)
    except Exception:  # pragma: no cover - defensive
        return 0


def ram_used_bytes() -> int:
    try:
        return int(psutil.virtual_memory().used)
    except Exception:  # pragma: no cover - defensive
        return 0


def disk_used_percent(path: str = "/") -> float:
    try:
        return float(shutil.disk_usage(path).percent)
    except OSError:  # pragma: no cover - path may be unreadable
        return 0.0


def network_bytes() -> tuple[int, int]:
    """Return cumulative (rx, tx) bytes across all NICs."""
    try:
        total = psutil.net_io_counters()
        return int(total.bytes_recv), int(total.bytes_sent)
    except Exception:  # pragma: no cover - defensive
        return 0, 0


def boot_time_utc() -> datetime:
    try:
        return datetime.fromtimestamp(psutil.boot_time(), tz=UTC)
    except Exception:  # pragma: no cover - defensive
        return datetime.now(UTC)


def system_uptime_seconds(now: datetime | None = None) -> float:
    """Return whole seconds since the last boot."""
    boot = boot_time_utc()
    return max(0.0, ((now or datetime.now(UTC)) - boot).total_seconds())