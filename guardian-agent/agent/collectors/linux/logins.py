"""Login and session collector.

Reports successful/failed authentication attempts and SSH/console sessions
found in ``/var/log/auth.log`` (or a configurable equivalent) and in the
``last`` history. Events are deduplicated by a stable signature so a re-run
does not re-emit the same session.

Parsing is deliberately tolerant: an unreadable or busy log file yields no
events instead of stopping the agent.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from agent.collectors.base import BaseCollector
from agent.collectors.linux.commands import CommandError, run_capture
from agent.core.types import RawObservation

_ACCEPTED_RE = re.compile(r"Accepted \w+ for (?P<user>\S+) from (?P<host>\S+) port (?P<port>\d+)")
_FAILED_RE = re.compile(r"Failed \w+ for (?P<user>\S+) from (?P<host>\S+) port (?P<port>\d+)")
_SESSION_RE = re.compile(r"session opened for user (?P<user>\S+) by \S+ \(uid (?P<uid>\d+)\)")

_AUTH_LOGS = (
    "/var/log/auth.log",
    "/var/log/secure",
)


class LoginCollector(BaseCollector):
    interval_seconds = 120

    def __init__(self, auth_logs: tuple[str, ...] = _AUTH_LOGS) -> None:
        super().__init__()
        self._auth_logs = auth_logs

    @property
    def name(self) -> str:
        return "logins"

    def collect(self, now: datetime) -> list[RawObservation]:
        observations: list[RawObservation] = self._parse_auth_logs()
        observations.extend(self._session_history())
        return observations

    def _parse_auth_logs(self) -> list[RawObservation]:
        observations: list[RawObservation] = []
        for line in self._tail_auth_lines(200):
            entry = self._parse_entry(line)
            if entry is None:
                continue
            signature = entry["event_type"] + ":" + str(entry["data"].get("timestamp"))
            if self._seen(signature):
                continue
            observations.append(entry)
        return observations

    def _tail_auth_lines(self, count: int) -> list[str]:
        for path in self._auth_logs:
            try:
                text = Path(path).read_text(encoding="utf-8", errors="replace")
                return text.splitlines()[-count:]
            except OSError:
                continue
        return []

    def _parse_entry(self, line: str) -> RawObservation | None:
        if "Accepted" in line:
            match = _ACCEPTED_RE.search(line)
            if match:
                return RawObservation(
                    event_type="login_success",
                    data={
                        "user": match.group("user"),
                        "source": match.group("host"),
                        "port": match.group("port"),
                        "timestamp": line[:17],
                        "method": "ssh",
                    },
                )
        if "Failed" in line:
            match = _FAILED_RE.search(line)
            if match:
                return RawObservation(
                    event_type="login_failed",
                    severity="warning",
                    data={
                        "user": match.group("user"),
                        "source": match.group("host"),
                        "port": match.group("port"),
                        "timestamp": line[:17],
                        "method": "ssh",
                    },
                )
        if "session opened" in line:
            match = _SESSION_RE.search(line)
            if match:
                return RawObservation(
                    event_type="session_opened",
                    data={
                        "user": match.group("user"),
                        "uid": match.group("uid"),
                        "timestamp": line[:17],
                    },
                )
        return None

    def _session_history(self) -> list[RawObservation]:
        try:
            raw = run_capture(["last", "-n", "25"], timeout=5.0)
        except CommandError:
            return []
        rows: list[RawObservation] = []
        for raw_line in raw.splitlines():
            line = raw_line.strip()
            if not line or line.startswith(("wtmp", "utmp")):
                continue
            if self._seen("last:" + line):
                continue
            rows.append(
                RawObservation(
                    event_type="session_history",
                    data={"user": line.split()[0] if line.split() else "", "line": line},
                )
            )
        return rows