"""
Prompt sanitization.

Never send JWTs, passwords, API keys, or other sensitive credentials to AI
providers. Before any user text leaves the application it is scrubbed for
high-signal secret shapes and replaced with a redaction marker.
"""

from __future__ import annotations

import re

REDACTED = "[REDACTED]"

_PATTERNS = (
    # JWT (three dot-separated base64url segments).
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    # OpenAI / generic `sk-` style keys.
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    # Google Gemini API keys.
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    # Anthropic-style keys.
    re.compile(r"\bsk-ant-[A-Za-z0-9_-]{12,}\b"),
    # Assignment of secrets: KEY/PASSWORD/SECRET/TOKEN = value.
    re.compile(
        r"(?i)\b(?:api[_-]?key|password|passwd|secret|token|credential)"
        r"\s*[:=]\s*\S{6,}",
    ),
    # Authorization / bearer headers.
    re.compile(r"(?i)\b(?:bearer|authorization)\s+[A-Za-z0-9._~+/=-]{16,}"),
    # Long opaque base64 blobs.
    re.compile(r"\b[A-Za-z0-9+/]{40,}={0,2}\b"),
)


def sanitize_prompt(text: str) -> str:
    """Redact high-signal secret shapes from free text."""

    if not text:
        return text

    scrubbed = text

    for pattern in _PATTERNS:
        scrubbed = pattern.sub(REDACTED, scrubbed)

    return scrubbed
