"""
Prompt construction for the Copilot.

System + user prompts are built from live estate context so every provider
(LLM or rules) works from the same structured data.
"""

import json

from app.copilot.intents import CopilotIntent

SYSTEM_PROMPT = (
    "You are GuardianX Copilot, a senior security analyst embedded in the "
    "GuardianX cyber defense platform. You help security teams understand "
    "their attack surface, findings, scans, and remediation priorities.\n\n"
    "Ground rules:\n"
    "- Base every answer on the provided STRUCTURED CONTEXT. Never invent "
    "assets, findings, scan counts, or scores that are not in the context.\n"
    "- If the context is empty or a referenced resource was not found, say "
    "so explicitly instead of guessing.\n"
    "- Format your answer in Markdown: short headings, bold key figures, "
    "and bullet lists where useful.\n"
    "- Be concise but complete. Use professional, technical language.\n"
    "- For remediation, give concrete, actionable steps (version updates, "
    "hardening, exposure reduction)."
)

INTENT_GUIDANCE = {
    CopilotIntent.EXPLAIN_CVE: (
        "Task: explain the referenced CVE. Cover what the vulnerability is, "
        "its severity and CVSS impact, and what it means for the affected "
        "assets listed in the context."
    ),
    CopilotIntent.EXPLAIN_VULNERABILITY: (
        "Task: explain the referenced vulnerability in plain terms. Cover "
        "what it is, why it is dangerous, its severity and CVSS impact, the "
        "affected asset and service, and how it was detected."
    ),
    CopilotIntent.ASSET_RISK: (
        "Task: explain why the referenced asset is risky. Use the severity "
        "breakdown, open ports, running services, findings, and risk score "
        "from the context."
    ),
    CopilotIntent.SCAN_SUMMARY: (
        "Task: summarize today's scans. Report totals by status, notable "
        "results, and findings discovered."
    ),
    CopilotIntent.ASSET_SUMMARY: (
        "Task: summarize the asset estate. Report total asset count, the "
        "breakdown by type and environment, and the most exposed assets "
        "from the context."
    ),
    CopilotIntent.REMEDIATION: (
        "Task: generate remediation guidance for the referenced finding. "
        "Prioritize concrete, actionable steps."
    ),
    CopilotIntent.PRIORITIZE: (
        "Task: prioritize the vulnerabilities. Order by severity and CVSS, "
        "justify the order, and call out the most urgent items."
    ),
    CopilotIntent.EXECUTIVE_SUMMARY: (
        "Task: generate an executive security summary for non-technical "
        "stakeholders. Lead with overall posture, then headline metrics and "
        "key risks."
    ),
    CopilotIntent.TECHNICAL_SUMMARY: (
        "Task: produce a SOC-friendly technical summary. Report the top "
        "findings with CVSS, EPSS and CISA KEV status, the affected assets, "
        "open ports and services, and concrete fixes. Use tables for the "
        "findings where useful."
    ),
    CopilotIntent.DASHBOARD_INSIGHTS: (
        "Task: generate dashboard insights. Cover the top five risks, the "
        "attack surface, the most vulnerable assets, security trends over "
        "time, and concrete improvement suggestions. Ground every claim in "
        "the provided trend and distribution data."
    ),
    CopilotIntent.THREAT_SUMMARY: (
        "Task: combine all available intelligence sources (NVD, CISA KEV, "
        "FIRST EPSS, MITRE ATT&CK, and VirusTotal when present) into one "
        "coherent explanation of the referenced CVE. Flag where sources "
        "agree or disagree and call out actively exploited conditions."
    ),
    CopilotIntent.NATURAL_LANGUAGE_SEARCH: (
        "Task: the user asked a natural-language question. A structured "
        "result set has already been queried from GuardianX. Summarize the "
        "results clearly, lead with the count of matching items, and list "
        "them concisely. If no results matched, say so and suggest a "
        "broader query."
    ),
    CopilotIntent.SECURITY_RECOMMENDATIONS: (
        "Task: produce prioritized security recommendations for the estate. "
        "Base them on the actual findings, exposed assets, open ports and "
        "services in the context. Group into quick wins and longer-term "
        "investments, and keep every recommendation concrete and actionable."
    ),
    CopilotIntent.GENERAL: (
        "Task: answer the user's security question using the provided "
        "context."
    ),
}


def build_system_prompt(
    intent: CopilotIntent,
    data: dict | None = None,
) -> str:
    guidance = INTENT_GUIDANCE.get(
        intent,
        INTENT_GUIDANCE[CopilotIntent.GENERAL],
    )
    return f"{SYSTEM_PROMPT}\n\n{guidance}"


def build_user_prompt(
    intent: CopilotIntent,
    message: str,
    data: dict,
) -> str:
    payload = {
        key: value
        for key, value in data.items()
        if key != "intent"
    }
    serialized = json.dumps(
        payload,
        default=str,
        indent=2,
    )
    return (
        f"## User request\n{message}\n\n"
        f"## STRUCTURED CONTEXT (JSON)\n"
        f"```json\n{serialized}\n```"
    )
