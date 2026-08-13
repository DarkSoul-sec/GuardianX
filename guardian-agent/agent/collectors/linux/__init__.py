"""Linux collector implementations.

Only the :class:`CollectorRegistry` factory and a per-platform builder live
here; the scheduler is platform agnostic. New platforms add an ``agent/
collectors/<platform>/`` package and feed the same registry.
"""

from __future__ import annotations

from agent.collectors.base import Collector
from agent.collectors.linux.file_integrity import FileIntegrityCollector
from agent.collectors.linux.logins import LoginCollector
from agent.collectors.linux.process import ProcessCollector
from agent.collectors.linux.services import ServiceCollector
from agent.collectors.linux.startup import StartupCollector
from agent.collectors.linux.system_health import SystemHealthCollector
from agent.collectors.linux.usb import UsbCollector


def linux_collectors() -> dict[str, Collector]:
    """Return the default set of Linux collectors keyed by collector name."""
    return {
        "process": ProcessCollector(),
        "system_health": SystemHealthCollector(),
        "logins": LoginCollector(),
        "services": ServiceCollector(),
        "file_integrity": FileIntegrityCollector(),
        "usb": UsbCollector(),
        "startup": StartupCollector(),
    }