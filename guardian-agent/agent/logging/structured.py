"""Structured, rotating logging.

Every record is emitted as a single JSON line (or human text), carries a UTC
timestamp, level, logger name and message, plus an optional ``request_id``
correlation id captured from :class:`agent.security` outbound calls.

The queue never receives passwords, tokens or other secrets — the codebase
passes plain ``message`` strings and no structured field is ever populated
with credential material.
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id",
    default=None,
)

_STANDARD_ATTRS = frozenset(
    {
        "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "taskName", "asctime", "message",
    }
)


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = request_id_var.get()
        if request_id:
            payload["request_id"] = request_id
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS:
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class ContextLogger(logging.LoggerAdapter):
    """Logger that attaches a fixed set of structured fields to every record."""

    def __init__(self, logger: logging.Logger, extra: dict[str, Any] | None = None) -> None:
        super().__init__(logger, extra or {})
        self._fields = dict(extra or {})

    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        extra = kwargs.setdefault("extra", {})
        for key, value in self._fields.items():
            extra.setdefault(key, value)
        return msg, kwargs

    def bind(self, **fields: Any) -> "ContextLogger":
        merged = dict(self._fields)
        merged.update(fields)
        return ContextLogger(self.logger, merged)


def configure_logging(
    level: str = "INFO",
    log_format: str = "json",
    log_dir: str | Path | None = None,
) -> None:
    """Configure the root handler with an optional rotating file handler."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(log_level)

    for handler in list(root.handlers):
        root.removeHandler(handler)

    formatter: logging.Formatter = (
        _JsonFormatter() if log_format.lower() == "json"
        else logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )

    if log_dir:
        directory = Path(log_dir)
        directory.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            directory / "guardian-agent.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    root.addHandler(stream)


def get_logger(name: str) -> ContextLogger:
    """Return a structured logger bound to a module name."""
    return ContextLogger(logging.getLogger(name))