"""
Per-user conversation memory for the Copilot.

Keeps a short, bounded, in-memory transcript per user so follow-up questions
("and what about its EPSS?") have context. Entries expire after a TTL and the
store is capped, so memory never grows unbounded or survives a restart. It is
deliberately ephemeral: conversation history is not persisted to the database.
"""

from __future__ import annotations

import time
from threading import Lock

from app.copilot.intents import CopilotIntent

_MEMORY_TTL_SECONDS = 1800
_MAX_TURNS_PER_USER = 12
_MAX_USERS = 1024

_store: dict[int, list[dict]] = {}
_lock = Lock()


def _purge(user_id: int) -> None:
    now = time.monotonic()
    turns = _store.get(user_id, [])

    retained = [
        turn
        for turn in turns
        if now - turn["at"] < _MEMORY_TTL_SECONDS
    ]

    if len(retained) != len(turns):
        _store[user_id] = retained


def push(
    user_id: int,
    role: str,
    content: str,
    intent: CopilotIntent | None = None,
    resolved: dict | None = None,
) -> None:
    """Append a single turn (user or assistant) to the user's memory."""

    with _lock:
        if len(_store) >= _MAX_USERS and user_id not in _store:
            _store.pop(next(iter(_store)), None)

        turns = _store.setdefault(user_id, [])
        turns.append(
            {
                "role": role,
                "content": content,
                "intent": intent.value if intent else None,
                "resolved": resolved or {},
                "at": time.monotonic(),
            }
        )

        if len(turns) > _MAX_TURNS_PER_USER:
            del turns[: len(turns) - _MAX_TURNS_PER_USER]


def recent(
    user_id: int,
    limit: int = 6,
) -> list[dict]:
    """Most recent turns for the user, oldest first, capped."""

    with _lock:
        _purge(user_id)
        turns = _store.get(user_id, [])[-limit:]

    return [
        {
            "role": turn["role"],
            "content": turn["content"],
            "intent": turn["intent"],
            "resolved": turn["resolved"],
        }
        for turn in turns
    ]


def build_recap(
    user_id: int,
    limit: int = 4,
) -> str:
    """
    Render the recent conversation as a compact prompt fragment.

    Only user turns and their resolved entities are included, so context is
    passed forward without echoing long assistant answers back into the model.
    """

    turns = recent(user_id, limit=limit)

    if not turns:
        return ""

    lines = ["Previous conversation context:"]
    for turn in turns:
        if turn["role"] != "user":
            continue
        context = turn["resolved"]
        if context:
            labels = [
                f"cve={context[c]}"
                for c in ("cve",)
                if context.get(c)
            ]
            if context.get("asset_name"):
                labels.append(f"asset={context['asset_name']}")
            if context.get("finding_title"):
                labels.append(f"finding={context['finding_title']}")
            suffix = f" [{', '.join(labels)}]" if labels else ""
        else:
            suffix = ""
        lines.append(f"- User: {turn['content']}{suffix}")

    return "\n".join(lines)


def clear(user_id: int) -> int:
    """Drop the user's memory. Returns the number of turns removed."""

    with _lock:
        turns = _store.pop(user_id, [])
    return len(turns)


def status(user_id: int) -> dict:
    """Lightweight memory status for debugging and the UI."""

    with _lock:
        _purge(user_id)
        turns = _store.get(user_id, [])

    return {
        "turns": len(turns),
        "ttl_seconds": _MEMORY_TTL_SECONDS,
    }
