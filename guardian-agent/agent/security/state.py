"""Persistent agent identity and credential state.

The agent stores its identity (``agent_id``), its provisioning registration
token and the current bearer tokens in a small JSON file with owner-only
permissions. Persistence is what allows the agent to recover credentials
across restarts without ever re-registering or storing a password.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from agent.core.types import AgentTokens


class CredentialState:
    """In-memory view of the persisted agent credential state."""

    def __init__(
        self,
        agent_id: str | None = None,
        agent_name: str | None = None,
        tokens: AgentTokens | None = None,
    ) -> None:
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.tokens = tokens

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CredentialState":
        tokens = None
        raw_tokens = payload.get("tokens")
        if raw_tokens:
            tokens = AgentTokens.model_validate(raw_tokens)
        return cls(
            agent_id=payload.get("agent_id"),
            agent_name=payload.get("agent_name"),
            tokens=tokens,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "tokens": self.tokens.model_dump(mode="json") if self.tokens else None,
        }


class StateStore:
    """Loads and atomically persists :class:`CredentialState` to disk."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def load(self) -> CredentialState:
        if not self._path.exists():
            return CredentialState()
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return CredentialState()
        return CredentialState.from_dict(payload)

    def save(self, state: CredentialState) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temp = self._path.with_suffix(".tmp")
        temp.write_text(json.dumps(state.to_dict()), encoding="utf-8")
        os.chmod(temp, 0o600)
        temp.replace(self._path)
        os.chmod(self._path, 0o600)