"""
Structured logging for GuardianX.

Log records are emitted as single-line JSON by default so they can be
consumed by log aggregators (Loki, ELK, CloudWatch, ...) without parsing
free-text patterns. Set ``LOG_FORMAT=text`` for human-friendly output.

Every record carries:

- a UTC ``timestamp``
- the ``level``
- the originating ``logger`` name
- the ``message``
- a ``request_id`` correlation id when the log originates inside an HTTP
  request (injected by ``app.middleware.request_log``)
- any ``extra={...}`` fields passed to the logging call

``logger`` remains the shared application logger used across the codebase.
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
from datetime import UTC, datetime

from app.core.config import settings

# Correlation id for the in-flight HTTP request, set by the request logging
# middleware and captured by the JSON formatter on every log record.
request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id",
    default=None,
)

# Attributes logging always sets on a LogRecord. Everything else that a
# caller passes via ``extra={...}`` is treated as structured context.
_STANDARD_ATTRS = frozenset(
    {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "taskName",
        "asctime",
        "message",
    }
)


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log record."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=UTC,
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = request_id_var.get()
        if request_id:
            payload["request_id"] = request_id

        for key, value in record.__dict__.items():
            if key in _STANDARD_ATTRS:
                continue
            payload[key] = value

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def _configure() -> None:
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    formatter = (
        JsonFormatter()
        if settings.LOG_FORMAT.lower() == "json"
        else logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s"
        )
    )

    root = logging.getLogger()
    root.setLevel(level)

    for handler in root.handlers:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root.addHandler(handler)

    # Keep the ASGI/uvicorn loggers from duplicating request lines; the
    # request logging middleware already emits one structured record.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(
        logging.DEBUG if settings.DEBUG else logging.WARNING
    )


_configure()

logger = logging.getLogger("guardianx")
