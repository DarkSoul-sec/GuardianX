"""Credential lifecycle management.

:class:`CredentialManager` owns the agent's identity lifecycle:

1. If no credentials exist, it boots in ``UNREGISTERED`` mode and performs a
   one-time registration using the provisioning ``registration_token``.
2. Once registered, it rotates the access token automatically by decoding the
   JWT ``exp`` claim and refreshing before expiry (never blocked on a 401).
3. It never sends a username or password; authentication is token based only.

The actual network calls are delegated to a :class:`TokenProvider` (implemented
by the HTTP transport) so this module stays pure and testable.
"""

from __future__ import annotations

from typing import Protocol

from agent.core.clock import Clock
from agent.core.types import AgentTokens
from agent.security.state import CredentialState, StateStore

_REFRESH_MARGIN_SECONDS = 60


class TokenProvider(Protocol):
    """HTTP transport capable of registering and refreshing an agent."""

    def register(self, *, agent_name: str, registration_token: str) -> AgentTokens: ...

    def refresh(self, agent_id: str, refresh_token: str) -> AgentTokens: ...


class CredentialManager:
    """Coordinates registration and token refresh for an agent."""

    def __init__(
        self,
        store: StateStore,
        clock: Clock,
        config_agent_name: str,
        registration_token: str | None,
        provider: TokenProvider | None = None,
    ) -> None:
        self._store = store
        self.provider = provider
        self._clock = clock
        self._config_agent_name = config_agent_name
        self._registration_token = registration_token
        self._state = store.load()

    @property
    def agent_id(self) -> str | None:
        return self._state.agent_id

    def ensure_registered(self) -> bool:
        """Register if needed and return whether an agent_id is now known."""
        if self._state.agent_id:
            return True
        if not self._registration_token:
            raise ValueError("no registration_token configured for a first registration")
        tokens = self.provider.register(
            agent_name=self._config_agent_name,
            registration_token=self._registration_token,
        )
        self._state = CredentialState(
            agent_id=tokens.agent_id,
            agent_name=self._config_agent_name,
            tokens=tokens,
        )
        self._store.save(self._state)
        return True

    def access_token(self) -> str | None:
        """Return a valid bearer token, refreshing it before it expires."""
        if self._state.tokens is None:
            return None
        if self._is_expiring(self._state.tokens):
            self._rotate()
        return self._state.tokens.access_token if self._state.tokens else None

    def force_refresh(self) -> None:
        """Rotate the access token immediately, e.g. on a server 401."""
        self._rotate()

    def _rotate(self) -> None:
        if self._state.tokens is None or not self._state.agent_id:
            return
        refreshed = self.provider.refresh(
            agent_id=self._state.agent_id,
            refresh_token=self._state.tokens.refresh_token,
        )
        if refreshed.token:
            self._state.tokens = refreshed
            self._store.save(self._state)

    def _is_expiring(self, tokens: AgentTokens) -> bool:
        remaining = (tokens.expires_at - self._clock.now()).total_seconds()
        return remaining < _REFRESH_MARGIN_SECONDS