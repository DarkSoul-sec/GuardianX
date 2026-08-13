"""USB device collector.

Watches the USB bus via ``/sys/bus/usb`` and reports insertions and removals
as they happen by diffing successive snapshots. Each device's vendor, product
and serial are read from sysfs attributes; the mount point (if any) is derived
from ``/proc/mounts``.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from agent.collectors.base import BaseCollector
from agent.core.types import RawObservation

_SYSFS_USB = Path("/sys/bus/usb/devices")
_ATTRS = ("idVendor", "idProduct", "manufacturer", "product", "serial")


class UsbCollector(BaseCollector):
    interval_seconds = 60

    def __init__(self, root: Path | None = None) -> None:
        super().__init__()
        self._root = root or _SYSFS_USB
        self._previous: dict[str, dict[str, Any]] = {}

    @property
    def name(self) -> str:
        return "usb"

    def collect(self, now: datetime) -> list[RawObservation]:
        current = {device: meta for device, meta in self._scan().items()}
        observations: list[RawObservation] = []

        if self._previous:
            for device, meta in current.items():
                if device not in self._previous:
                    observations.append(
                        RawObservation(event_type="usb_inserted", data=meta)
                    )
            for device in self._previous:
                if device not in current:
                    observations.append(
                        RawObservation(
                            event_type="usb_removed",
                            severity="warning",
                            data={"device": device, **self._previous[device]},
                        )
                    )

        self._previous = current
        return observations

    def _scan(self) -> dict[str, dict[str, Any]]:
        if not self._root.is_dir():
            return {}
        result: dict[str, dict[str, Any]] = {}
        try:
            entries = sorted(self._root.iterdir())
        except OSError:
            return result

        mounts = self._mount_map()

        for node in entries:
            if not node.is_dir():
                continue
            identifiers = {name: _read_attr(node / name) for name in _ATTITRS}
            if not identifiers["idVendor"] and not identifiers["idProduct"]:
                continue
            device = node.name
            meta: dict[str, Any] = {
                "path": f"/dev/{device}",
                **{k: v for k, v in identifiers.items() if v is not None},
            }
            mount = mounts.get(meta.get("path"))
            if mount:
                meta["mount_point"] = mount
            result[device] = meta
        return result

    def _mount_map(self) -> dict[str, str]:
        mount_map: dict[str, str] = {}
        try:
            with open("/proc/mounts", encoding="utf-8") as handle:
                for line in handle:
                    parts = line.split()
                    if len(parts) >= 2:
                        mount_map[parts[0]] = parts[1]
        except OSError:
            pass
        return mount_map


def _read_attr(path: Path) -> str | None:
    try:
        value = path.read_text(encoding="utf-8", errors="replace").strip()
        return value or None
    except OSError:
        return None