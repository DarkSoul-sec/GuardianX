"""
Simple in-memory rate limiter.

A per-client fixed-window counter that rejects requests past the configured
per-minute budget. Suitable for a single-process deployment; a distributed
limiter (e.g. Redis) would be needed behind multiple workers.
"""

from __future__ import annotations

import time

from starlette.responses import JSONResponse

from app.logger import logger

_WINDOW_SECONDS = 60
_MAX_CLIENTS = 10_000


class RateLimitMiddleware:
    def __init__(
        self,
        app,
        enabled: bool,
        per_minute: int,
    ) -> None:
        self.app = app
        self.enabled = enabled
        self.limit = max(1, per_minute)
        self._hits: dict[str, tuple[float, int]] = {}

    def _allow(self, client_ip: str) -> bool:
        now = time.monotonic()

        if len(self._hits) > _MAX_CLIENTS:
            self._prune(now)

        window_start, count = self._hits.get(client_ip, (now, 0))

        if now - window_start >= _WINDOW_SECONDS:
            window_start = now
            count = 0

        if count >= self.limit:
            return False

        self._hits[client_ip] = (window_start, count + 1)

        return True

    def _prune(self, now: float) -> None:
        expired = [
            client
            for client, (window_start, _) in self._hits.items()
            if now - window_start >= _WINDOW_SECONDS
        ]

        for client in expired:
            self._hits.pop(client, None)

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http" or not self.enabled:
            await self.app(scope, receive, send)
            return

        client = scope.get("client")
        client_ip = client[0] if client else "unknown"

        if not self._allow(client_ip):
            logger.warning(
                "Rate limit exceeded for client %s.",
                client_ip,
            )

            response = JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again shortly.",
                    "code": "rate_limited",
                },
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
