"""
Adds baseline security headers to every HTTP response.
"""

from __future__ import annotations

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'",
}


class SecurityHeadersMiddleware:
    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message) -> None:
            if message["type"] == "http.response.start":
                headers = message.get("headers", [])
                header_keys = {key.lower() for key, _ in headers}
                extra = [
                    (name.encode("latin-1"), value.encode("latin-1"))
                    for name, value in _SECURITY_HEADERS.items()
                    if name.lower() not in header_keys
                ]
                message = {
                    **message,
                    "headers": [*headers, *extra],
                }

            await send(message)

        await self.app(scope, receive, send_with_headers)
