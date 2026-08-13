"""
Concise asset summary used on the asset detail page.

When a real AI provider is configured the summary is generated through the
Copilot pipeline; otherwise a deterministic, data-driven summary is used.
Generation is cached per asset, bounded in time, and never raises.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

from app.copilot.factory import get_copilot_provider
from app.logger import logger

_SUMMARY_TIMEOUT_SECONDS = 8
_CACHE_TTL_SECONDS = 600
_MAX_CACHE_ENTRIES = 512

_executor = ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="ai-summary",
)

_cache: dict[int, tuple[float, str]] = {}

_SYSTEM_PROMPT = (
    "You are the GuardianX security copilot. Summarize an asset's risk "
    "posture in one or two concise sentences for a security dashboard. "
    "Be factual, use only the provided data, and do not invent findings."
)


def _heuristic_summary(stats: dict) -> str:
    name = stats.get("name") or "This asset"
    total = stats.get("total_findings", 0)
    open_ports = stats.get("open_ports", [])
    internet_facing = stats.get("internet_facing", False)

    exposure = "exposed to the internet" if internet_facing else "internal"
    port_text = (
        f"{len(open_ports)} open port(s)"
        if open_ports
        else "no open ports"
    )
    finding_text = (
        f"{total} known finding(s)"
        if total
        else "no known findings"
    )

    return (
        f"GuardianX assessed {name} as an {exposure} asset with "
        f"{port_text} and {finding_text}."
    )


def _build_prompt(stats: dict) -> str:
    open_ports = ", ".join(str(port) for port in stats.get("open_ports", [])) or "none"
    technologies = ", ".join(stats.get("technologies", [])) or "none"

    return (
        f"Asset: {stats.get('name')}\n"
        f"Type: {stats.get('asset_type')}\n"
        f"IP: {stats.get('ip_address')}\n"
        f"Environment: {stats.get('environment')}\n"
        f"Criticality: {stats.get('criticality')}\n"
        f"Internet facing: {stats.get('internet_facing')}\n"
        f"Risk score: {stats.get('risk_score')}/100\n"
        f"Attack surface score: {stats.get('attack_surface_score')}/100\n"
        f"Findings: {stats.get('total_findings')} total "
        f"(critical {stats.get('critical')}, high {stats.get('high')}, "
        f"medium {stats.get('medium')}, low {stats.get('low')})\n"
        f"Open ports: {open_ports}\n"
        f"Technologies: {technologies}\n"
        "Write a concise 1-2 sentence summary of this asset's risk posture."
    )


def _normalize(text: str) -> str:
    return " ".join(text.split())


def generate_asset_summary(asset_id: int, stats: dict) -> str:
    """
    Return a concise summary for the given asset.

    Uses the configured Copilot provider when one is available, falling
    back to a deterministic summary on any failure or timeout.
    """

    now = time.monotonic()

    cached = _cache.get(asset_id)
    if cached and cached[0] > now:
        return cached[1]

    provider = get_copilot_provider()
    summary = _heuristic_summary(stats)

    if provider.name != "rules":
        future = _executor.submit(
            provider.complete,
            _SYSTEM_PROMPT,
            _build_prompt(stats),
        )

        try:
            result = future.result(
                timeout=_SUMMARY_TIMEOUT_SECONDS,
            )

            if result and result.strip():
                summary = _normalize(result)
        except Exception:
            logger.warning(
                "AI summary failed for asset %s; using heuristic.",
                asset_id,
            )

    if len(_cache) >= _MAX_CACHE_ENTRIES:
        _cache.clear()

    _cache[asset_id] = (now + _CACHE_TTL_SECONDS, summary)

    return summary
