"""File integrity collector.

Snapshots a set of directories (default: ``/etc``, ``/usr/bin``,
``/usr/local/bin``) and reports created, deleted, modified, permission-changed
and hash-changed files by comparing successive runs against cached state.

For efficiency the collector hashes only regular files up to a size cap and
skips the volatile ``/proc``, ``/sys`` and ``/dev`` mount roots wherever they
appear. It never opens files with write access and never alters anything.
"""

from __future__ import annotations

import hashlib
import stat as stat_module
from datetime import datetime
from pathlib import Path
from typing import Any

from agent.collectors.base import BaseCollector
from agent.core.types import RawObservation

_DEFAULT_DIRS = ("/etc", "/usr/bin", "/usr/local/bin")
_SKIP_NAMES = {"/proc", "/sys", "/dev", "/run"}
_MAX_HASH_BYTES = 5 * 1024 * 1024


class FileIntegrityCollector(BaseCollector):
    interval_seconds = 600

    def __init__(self, directories: tuple[str, ...] = _DEFAULT_DIRS) -> None:
        super().__init__()
        self._directories = directories
        self._baseline: dict[str, dict[str, Any]] = {}

    @property
    def name(self) -> str:
        return "file_integrity"

    def collect(self, now: datetime) -> list[RawObservation]:
        current = self._snapshot()
        observations: list[RawObservation] = []

        if self._baseline:
            for path, meta in current.items():
                previous = self._baseline.get(path)
                if previous is None:
                    observations.append(self._change("created", path, meta))
                    continue
                if previous["hash"] != meta["hash"]:
                    observations.append(self._change("hash_changed", path, meta))
                elif previous["mtime"] != meta["mtime"]:
                    observations.append(self._change("modified", path, meta))
                elif previous["mode"] != meta["mode"]:
                    observations.append(self._change("permission_changed", path, meta))

            for path in self._baseline:
                if path not in current:
                    observations.append(
                        RawObservation(
                            event_type="file_integrity",
                            severity="warning",
                            data={"action": "deleted", "path": path},
                        )
                    )

        self._baseline = current
        return observations

    def _snapshot(self) -> dict[str, dict[str, Any]]:
        snapshot: dict[str, dict[str, Any]] = {}
        for directory in self._directories:
            self._snapshot_dir(Path(directory), snapshot)
        return snapshot

    def _snapshot_dir(self, root: Path, snapshot: dict[str, dict[str, Any]]) -> None:
        if not root.is_dir():
            return
        try:
            iterator = root.rglob("*")
        except OSError:
            return
        for entry in iterator:
            name = entry.name
            if name in _SKIP_NAMES:
                continue
            try:
                if entry.is_symlink() or not entry.is_file():
                    continue
                meta = self._describe(entry)
                if meta is not None:
                    snapshot[str(entry)] = meta
            except OSError:
                continue

    def _describe(self, path: Path) -> dict[str, Any] | None:
        try:
            info = path.stat()
        except OSError:
            return None
        if not stat_module.S_ISREG(info.st_mode):
            return None
        return {
            "path": str(path),
            "size": info.st_size,
            "mtime": info.st_mtime,
            "mode": info.st_mode,
            "hash": self._file_hash(path, info),
            "owner_uid": info.st_uid,
        }

    def _file_hash(self, path: Path, info: Any) -> str | None:
        if info.st_size > _MAX_HASH_BYTES:
            return None
        digest = hashlib.sha256()
        try:
            with open(path, "rb") as handle:
                for block in iter(lambda: handle.read(65536), b""):
                    digest.update(block)
        except OSError:
            return None
        return digest.hexdigest()

    def _change(self, action: str, path: str, meta: dict[str, Any]) -> RawObservation:
        return RawObservation(
            event_type="file_integrity",
            severity=("warning" if action != "created" else "info"),
            data={
                "action": action,
                "path": path,
                "hash": meta.get("hash"),
                "size": meta.get("size"),
                "mode": meta.get("mode"),
            },
        )