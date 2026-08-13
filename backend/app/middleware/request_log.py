"""
Structured HTTP request logging.

Emits one structured record per request with a correlation id, method,
path, client IP, HTTP status and duration. The correlation id is stored
in a context variable so every log line produced while handling the
request is tied to the same ``request_id``.
"""

from __future__ import annotations

import time
import uuid

from app.logger import logger, request_id_var


class RequestLoggingMiddleware:
    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        request_id = uuid.uuid4().hex[:12]
        method = scope.get("method", "?")
        path = scope.get("path", "?")
        client = scope.get("client")
        client_ip = client[0] if client else None

        token = request_id_var.set(request_id)

        async def send_wrapper(message) -> None:
            if message["type"] == "http.response.start":
                duration_ms = round(
                    (time.perf_counter() - start) * 1000,
                    2,
                )
                logger.info(
                    "request completed",
                    extra={
                        "request_id": request_id,
                        "method": method,
                        "path": path,
                        "client_ip": client_ip,
                        "status": message["status"],
                        "duration_ms": duration_ms,
                    },
                )
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            request_id_var.reset(token)
