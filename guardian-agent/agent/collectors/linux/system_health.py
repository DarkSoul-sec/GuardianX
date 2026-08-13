"""System health collector.

A periodic snapshot of CPU, RAM, disk, network, load average, uptime,
hostname and kernel version. Emits one ``system_health`` observation each
run, which is what feeds the dashboard's health metrics.
"""

from __future__ import annotations

from datetime import datetime

import psutil

from agent.collectors.base import BaseCollector
from agent.collectors.linux import system as system_info
from agent.core.types import RawObservation


class SystemHealthCollector(BaseCollector):
    interval_seconds = 60

    @property
    def name(self) -> str:
        return "system_health"

    def collect(self, now: datetime) -> list[RawObservation]:
        rx, tx = system_info.network_bytes()
        load1, load5, load15 = system_info.load_average()
        vm = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        data = {
            "hostname": system_info.hostname(),
            "os": system_info.os_name(),
            "kernel_version": system_info.kernel_version(),
            "uptime_seconds": system_info.system_uptime_seconds(now),
            "cpu_percent": system_info.cpu_percent(),
            "load_average": {"1m": load1, "5m": load5, "15m": load15},
            "ram": {
                "total_bytes": vm.total,
                "used_bytes": vm.used,
                "percent": vm.percent,
            },
            "disk": {
                "total_bytes": disk.total,
                "used_bytes": disk.used,
                "percent": disk.percent,
            },
            "network": {"rx_bytes": rx, "tx_bytes": tx},
        }

        return [RawObservation(event_type="system_health", data=data)]