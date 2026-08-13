"""
Copilot intents: the discrete capabilities the assistant can perform.
"""

from enum import Enum
import re


class CopilotIntent(str, Enum):
    EXPLAIN_CVE = "explain_cve"
    EXPLAIN_VULNERABILITY = "explain_vulnerability"
    ASSET_RISK = "asset_risk"
    SCAN_SUMMARY = "scan_summary"
    ASSET_SUMMARY = "asset_summary"
    REMEDIATION = "remediation"
    PRIORITIZE = "prioritize"
    EXECUTIVE_SUMMARY = "executive_summary"
    TECHNICAL_SUMMARY = "technical_summary"
    DASHBOARD_INSIGHTS = "dashboard_insights"
    THREAT_SUMMARY = "threat_summary"
    NATURAL_LANGUAGE_SEARCH = "natural_language_search"
    SECURITY_RECOMMENDATIONS = "security_recommendations"
    GENERAL = "general"


CVE_PATTERN = re.compile(
    r"\bCVE-\d{4}-\d{4,7}\b",
    re.IGNORECASE,
)

_SEARCH_VERBS = (
    "show",
    "find",
    "list",
    "display",
    "get me",
    "give me",
    "what assets",
    "which assets",
    "what servers",
    "which servers",
    "how many",
    "search for",
    "find all",
    "show me",
)

_SEARCH_SERVICE_HINTS = (
    "ssh",
    "postgres",
    "postgresql",
    "mysql",
    "mariadb",
    "redis",
    "mongodb",
    "elastic",
    "apache",
    "nginx",
    "iis",
    "ftp",
    "sftp",
    "smtp",
    "imap",
    "pop3",
    "rdp",
    "snmp",
    "ldap",
    "telnet",
    "web server",
    "database",
    "docker",
    "kubernetes",
    "kafka",
    "rabbitmq",
    "memcached",
    "oracle",
    "sql server",
    "dns",
    "nfs",
)


def _looks_like_search_query(text: str) -> bool:
    """
    Conservative heuristic: a natural-language query asks to show/list/find
    estate objects (assets, findings, services, ports) in plain words.
    """

    lowered = text.strip()

    if not lowered or len(lowered.split()) < 2:
        return False

    if any(verb in lowered for verb in _SEARCH_VERBS):
        return True

    if any(hint in lowered for hint in _SEARCH_SERVICE_HINTS):
        return True

    if any(
        severity in lowered
        for severity in ("critical", "high", "medium", "low")
    ) and "vulnerab" in lowered:
        return True

    if "exposed" in lowered and any(
        hint in lowered
        for hint in ("port", "service", "ssh", "rdp", "web", "http", "https")
    ):
        return True

    return False


def extract_cve(message: str | None) -> str | None:
    """
    Pull the first CVE identifier out of a free-text message.
    """

    if not message:
        return None

    match = CVE_PATTERN.search(message)

    return match.group(0).upper() if match else None


def detect_intent(
    message: str,
    asset_id: int | None = None,
    finding_id: int | None = None,
) -> CopilotIntent:
    """
    Heuristically map free text to a CopilotIntent.

    Explicit context (asset/finding ids or a CVE in the text) takes
    priority over keyword matching so entity-backed intents win.
    """

    text = (message or "").lower()

    if finding_id or any(
        keyword in text
        for keyword in ("remediat", "mitigat", "patch", "fix it", "fixing")
    ):
        return CopilotIntent.REMEDIATION

    if any(
        keyword in text
        for keyword in (
            "threat summary",
            "combine",
            "all sources",
            "full threat picture",
            "merge intelligence",
            "correlate",
        )
    ) and extract_cve(message):
        return CopilotIntent.THREAT_SUMMARY

    if extract_cve(message):
        return CopilotIntent.EXPLAIN_CVE

    if any(
        keyword in text
        for keyword in (
            "explain this vulnerability",
            "explain the vulnerability",
            "explain vulnerability",
            "what is this vulnerability",
            "describe this vulnerability",
            "vulnerability details",
            "explain this finding",
            "explain the finding",
            "finding details",
        )
    ) or (
        finding_id
        and any(
            keyword in text
            for keyword in ("explain", "what is", "describe", "detail", "why")
        )
    ):
        return CopilotIntent.EXPLAIN_VULNERABILITY

    if any(
        keyword in text
        for keyword in ("prioriti", "rank", "triage", "most urgent")
    ):
        return CopilotIntent.PRIORITIZE

    if any(
        keyword in text
        for keyword in (
            "technical summary",
            "soc report",
            "soc-friendly",
            "technical report",
            "technical overview",
        )
    ):
        return CopilotIntent.TECHNICAL_SUMMARY

    if any(
        keyword in text
        for keyword in (
            "dashboard insights",
            "security trends",
            "top risks",
            "top 5 risks",
            "most vulnerable assets",
            "attack surface",
            "improvement suggestions",
            "insights",
            "estate trends",
        )
    ):
        return CopilotIntent.DASHBOARD_INSIGHTS

    if "scan" in text and any(
        keyword in text
        for keyword in ("summar", "today", "latest", "run", "result")
    ):
        return CopilotIntent.SCAN_SUMMARY

    if any(
        keyword in text
        for keyword in ("asset summary", "summarize the assets", "summarise the assets")
    ) or (
        "asset" in text
        and "summar" in text
    ):
        return CopilotIntent.ASSET_SUMMARY

    if any(
        keyword in text
        for keyword in ("executive", "posture", "board", "stakeholder", "high-level")
    ) or text == "summary":
        return CopilotIntent.EXECUTIVE_SUMMARY

    if any(
        keyword in text
        for keyword in (
            "security recommendations",
            "security recommendation",
            "recommendations",
            "recommendation",
            "recommend",
            "best practices",
            "best practice",
            "hardening",
            "guardrails",
            "improve my security",
            "improve security posture",
            "what should i do",
        )
    ):
        return CopilotIntent.SECURITY_RECOMMENDATIONS

    if asset_id or (
        "asset" in text
        and any(keyword in text for keyword in ("risk", "risky", "why", "expos"))
    ):
        return CopilotIntent.ASSET_RISK

    if _looks_like_search_query(text):
        return CopilotIntent.NATURAL_LANGUAGE_SEARCH

    return CopilotIntent.GENERAL
