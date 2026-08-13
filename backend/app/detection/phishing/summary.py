"""
Human-readable summary generation for phishing analyses.

When a real AI provider is configured the summary is generated through the
shared Copilot provider pipeline; otherwise a deterministic, data-driven
summary is used. Generation is bounded in time and never raises, mirroring
the pattern used for asset summaries in ``app.copilot.summary``.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from app.copilot.factory import get_copilot_provider
from app.logger import logger

_SUMMARY_TIMEOUT_SECONDS = 10

_executor = ThreadPoolExecutor(
    max_workers=1,
    thread_name_prefix="phishing-summary",
)

_SYSTEM_PROMPT = (
    "You are the GuardianX security copilot. Summarize the phishing risk of "
    "a URL in one or two concise sentences for a security analyst. Use only "
    "the provided data, do not invent findings, and state the risk level first."
)


def _heuristic_summary(url: str, threat_score: int, risk_level: str, reasons: list[str]) -> str:
    prefix = (
        f"GuardianX assessed {url} as {risk_level.upper()} risk "
        f"({threat_score}/100)."
    )

    if not reasons:
        return f"{prefix} No significant phishing indicators were detected."

    return f"{prefix} Primary concern: {reasons[0]}."


def _build_prompt(
    url: str,
    threat_score: int,
    risk_level: str,
    reasons: list[str],
    recommendations: list[str],
    checks: list[dict],
) -> str:
    lines = [
        f"URL: {url}",
        f"Threat score: {threat_score}/100",
        f"Risk level: {risk_level}",
        "Reasons:",
    ]

    lines += [f"- {reason}" for reason in reasons] or ["- none"]

    lines.append("Recommendations:")

    lines += [f"- {recommendation}" for recommendation in recommendations] or ["- none"]

    lines.append("Top checks:")

    lines += [
        f"- {check.get('check')}: {check.get('score')}/100 ({check.get('reason')})"
        for check in checks[:6]
    ]

    lines.append("Write a concise 1-2 sentence summary of the phishing risk.")

    return "\n".join(lines)


def generate_phishing_summary(
    url: str,
    threat_score: int,
    risk_level: str,
    reasons: list[str],
    recommendations: list[str],
    checks: list[dict],
    enabled: bool,
) -> str:
    """
    Return a concise summary for a phishing analysis.

    Uses the configured Copilot provider when one is available, falling back
    to a deterministic summary on any failure or timeout.
    """
    summary = _heuristic_summary(url, threat_score, risk_level, reasons)

    if not enabled:
        return summary

    provider = get_copilot_provider()

    if provider.name == "rules":
        return summary

    future = _executor.submit(
        provider.complete,
        _SYSTEM_PROMPT,
        _build_prompt(url, threat_score, risk_level, reasons, recommendations, checks),
    )

    try:
        result = future.result(timeout=_SUMMARY_TIMEOUT_SECONDS)

        if result and result.strip():
            return " ".join(result.split())
    except Exception:
        logger.warning("AI phishing summary failed; using heuristic.")

    return summary
