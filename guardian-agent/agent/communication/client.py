"""The Guardian API transport.

The agent's only outbound HTTP path. It:
- talks HTTPS (or HTTP in local development), JSON payloads
- compresses telemetry batches with gzip
- reuses a pooled httpx connection
- times out and retries transient transport failures
- correlates every request with ``X-Request-Id``
- authenticates with the bearer token from the credential manager

It also implements :class:`~agent.security.manager.TokenProvider`, so
registration and refresh share the same transport.
"""

from __future__ import annotations

import gzip
import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from agent.config.loader import AgentConfig
from agent.core.types import AgentTokens
from agent.logging.structured import get_logger, request_id_var
from agent.security.manager import CredentialManager

log = get_logger("agent.communication")


class GuardianError(Exception):
    """Raised when the platform rejects (4xx/5xx) or the request cannot be made."""


class GuardianUnauthorized(GuardianError):
    """Raised when the platform returns HTTP 401 for an agent request."""


def _tokens_from_response(data: dict[str, Any], now: datetime) -> AgentTokens:
    seconds = int(data.get("expires_in", 0))
    return AgentTokens(
        agent_id=str(data["agent_id"]),
        access_token=str(data["access_token"]),
        refresh_token=str(data["refresh_token"]),
        expires_at=(now + timedelta(seconds=seconds)),
    )


class ApiClient:
    """Authenticated HTTP client for the Guardian agent endpoints."""

    def __init__(self, config: AgentConfig, credentials: CredentialManager) -> None:
        self._credentials = credentials
        transport = httpx.HTTPTransport(retries=config.max_retries)
        self._client = httpx.Client(
            base_url=config.server_url,
            timeout=httpx.Timeout(
                connect=config.connect_timeout,
                read=config.request_timeout,
                write=config.request_timeout,
                pool=config.connect_timeout,
            ),
            transport=transport,
            verify=config.tls_verify,
        )

    def register(self, agent_name: str, registration_token: str) -> AgentTokens:
        data = self._post(
            "/agents/register",
            payload={"agent_name": agent_name},
            extra_headers={"X-Registration-Token": registration_token},
        )
        return _tokens_from_response(data, datetime.now(UTC))

    def refresh(self, agent_id: str, refresh_token: str) -> AgentTokens:
        data = self._post(
            "/agents/refresh",
            payload={"agent_id": agent_id, "refresh_token": refresh_token},
        )
        return _tokens_from_response(data, datetime.now(UTC))

    def send_heartbeat(self, payload: dict[str, Any]) -> None:
        self._authorized_post("/agents/heartbeat", payload)

    def send_events(self, events: list[dict[str, Any]]) -> int:
        body = gzip.compress(json.dumps(events).encode("utf-8"))
        data = self._authorized_post(
            "/agents/events",
            payload=body,
            content_encoding="gzip",
        )
        return int(data.get("accepted", len(events)))

    def close(self) -> None:
        self._client.close()

    def _authorized_post(
        self,
        path: str,
        payload: Any,
        content_encoding: str | None = None,
    ) -> dict[str, Any]:
        try:
            return self._post(path, payload=payload, content_encoding=content_encoding, authorized=True)
        except GuardianUnauthorized:
            log.warning("token rejected; rotating and retrying once")
            self._credentials.force_refresh()
            return self._post(path, payload=payload, content_encoding=content_encoding, authorized=True)

    def _post(
        self,
        path: str,
        payload: Any,
        extra_headers: dict[str, str] | None = None,
        content_encoding: str | None = None,
        authorized: bool = False,
    ) -> dict[str, Any]:
        request_id = uuid.uuid4().hex
        headers = dict(extra_headers or {})
        headers["X-Request-Id"] = request_id
        headers["Content-Type"] = "application/json"

        if authorized:
            token = self._credentials.access_token()
            if not token:
                raise GuardianError("no access token available")
            headers["Authorization"] = f"Bearer {token}"

        if content_encoding:
            headers["Content-Encoding"] = content_encoding
            content = payload if isinstance(payload, bytes) else json.dumps(payload)
        else:
            content = json.dumps(payload)

        token_context = request_id_var.set(request_id)
        try:
            try:
                response = self._client.post(path, content=content, headers=headers)
            except httpx.HTTPError as exc:
                raise GuardianError(f"transport error: {exc}") from exc
        finally:
            request_id_var.reset(token_context)

        return _decode_response(response, authorized=authorized)


def _decode_response(response: httpx.Response, *, authorized: bool) -> dict[str, Any]:
    if response.status_code == 401 and authorized:
        raise GuardianUnauthorized("unauthorized")

    try:
        data = response.json()
    except (json.JSONDecodeError, ValueError):
        data = {}

    if response.status_code >= 400:
        log.error("platform error status=%s body=%s", response.status_code, response.text[:200])
        raise GuardianError(
            f"platform returned HTTP {response.status_code}: {response.text[:200]}"
        )
    return data if isinstance(data, dict) else {}