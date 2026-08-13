"""MITRE ATT&CK technique mapping.

CVEs do not carry native ATT&CK technique ids, so GuardianX maps each
CVE's CWE weaknesses to the techniques an attacker most commonly uses to
exploit that weakness class. The technique catalog below is a curated
subset of ATT&CK (Enterprise) covering the techniques referenced by the
CWE mapping, exposed through :func:`get_techniques`.

The mapping and catalog are plain data so they can be extended or tuned
without touching any logic.
"""

from __future__ import annotations

from typing import Any


ATTACK_TECHNIQUES: dict[str, dict[str, Any]] = {
    "T1190": {
        "id": "T1190",
        "name": "Exploit Public-Facing Application",
        "tactics": ["Initial Access"],
        "description": (
            "Adversaries exploit weaknesses in internet-facing software to "
            "gain initial access to an asset."
        ),
    },
    "T1059": {
        "id": "T1059",
        "name": "Command and Scripting Interpreter",
        "tactics": ["Execution"],
        "description": (
            "Adversaries abuse command and scripting interpreters to "
            "execute arbitrary code."
        ),
    },
    "T1059.007": {
        "id": "T1059.007",
        "name": "JavaScript",
        "tactics": ["Execution"],
        "description": (
            "Adversaries execute JavaScript in browser or runtime contexts, "
            "often to deliver malicious web content."
        ),
    },
    "T1203": {
        "id": "T1203",
        "name": "Exploitation for Client Execution",
        "tactics": ["Execution"],
        "description": (
            "Adversaries exploit a client-side vulnerability to execute "
            "code on a victim's system."
        ),
    },
    "T1204": {
        "id": "T1204",
        "name": "User Execution",
        "tactics": ["Execution"],
        "description": (
            "Adversaries rely on a user performing an action (clicking a "
            "link, opening a file) to trigger malicious behavior."
        ),
    },
    "T1078": {
        "id": "T1078",
        "name": "Valid Accounts",
        "tactics": ["Defense Evasion", "Persistence", "Privilege Escalation", "Initial Access"],
        "description": (
            "Adversaries steal or abuse legitimate credentials to access "
            "systems and bypass controls."
        ),
    },
    "T1068": {
        "id": "T1068",
        "name": "Exploitation for Privilege Escalation",
        "tactics": ["Privilege Escalation"],
        "description": (
            "Adversaries exploit a vulnerability to gain higher privileges "
            "on a system."
        ),
    },
    "T1505.003": {
        "id": "T1505.003",
        "name": "Web Shell",
        "tactics": ["Persistence"],
        "description": (
            "Adversaries upload a web shell to maintain persistent remote "
            "access through a web server."
        ),
    },
    "T1566": {
        "id": "T1566",
        "name": "Phishing",
        "tactics": ["Initial Access"],
        "description": (
            "Adversaries send targeted messages that trick users into "
            "disclosing credentials or running malicious content."
        ),
    },
    "T1005": {
        "id": "T1005",
        "name": "Data from Local System",
        "tactics": ["Collection"],
        "description": (
            "Adversaries collect sensitive data stored on local systems."
        ),
    },
    "T1530": {
        "id": "T1530",
        "name": "Data from Network Shared Drive",
        "tactics": ["Collection"],
        "description": (
            "Adversaries collect sensitive data from network shared drives."
        ),
    },
    "T1557": {
        "id": "T1557",
        "name": "Adversary-in-the-Middle",
        "tactics": ["Collection", "Credential Access"],
        "description": (
            "Adversaries position themselves between two communicating "
            "parties to intercept or alter traffic."
        ),
    },
    "T1083": {
        "id": "T1083",
        "name": "File and Directory Discovery",
        "tactics": ["Discovery"],
        "description": (
            "Adversaries enumerate files and directories to understand the "
            "target environment."
        ),
    },
}


CWE_TO_ATTACK_TECHNIQUES: dict[str, list[str]] = {
    "CWE-79": ["T1059.007", "T1204", "T1566"],
    "CWE-89": ["T1190", "T1059"],
    "CWE-78": ["T1190", "T1059"],
    "CWE-77": ["T1190", "T1059"],
    "CWE-94": ["T1190", "T1059"],
    "CWE-434": ["T1190", "T1505.003"],
    "CWE-287": ["T1078", "T1190"],
    "CWE-306": ["T1078", "T1190"],
    "CWE-862": ["T1078"],
    "CWE-863": ["T1078"],
    "CWE-798": ["T1078"],
    "CWE-352": ["T1204", "T1190"],
    "CWE-601": ["T1566"],
    "CWE-22": ["T1190", "T1083"],
    "CWE-23": ["T1190", "T1083"],
    "CWE-502": ["T1059", "T1203"],
    "CWE-918": ["T1190"],
    "CWE-611": ["T1190", "T1203"],
    "CWE-200": ["T1005", "T1530"],
    "CWE-326": ["T1557"],
    "CWE-119": ["T1203", "T1068"],
    "CWE-120": ["T1203", "T1068"],
    "CWE-125": ["T1203", "T1068"],
    "CWE-190": ["T1203", "T1068"],
    "CWE-416": ["T1203", "T1068"],
    "CWE-787": ["T1203", "T1068"],
    "CWE-269": ["T1068"],
}


def get_techniques(tactic: str | None = None) -> list[dict]:
    """Return the ATT&CK technique catalog, optionally filtered by tactic."""

    techniques = list(ATTACK_TECHNIQUES.values())

    if tactic:
        needle = tactic.strip().lower()
        techniques = [
            technique
            for technique in techniques
            if any(
                group.lower() == needle
                for group in technique["tactics"]
            )
        ]

    return sorted(techniques, key=lambda technique: technique["id"])


def map_cwes_to_techniques(cwes: list[str]) -> list[dict]:
    """Resolve a list of CWE ids to the matching ATT&CK techniques."""

    matched: list[dict] = []
    seen: set[str] = set()

    for cwe in cwes:
        cwe_id = cwe.strip().upper()
        for technique_id in CWE_TO_ATTACK_TECHNIQUES.get(cwe_id, []):
            if technique_id in seen:
                continue
            technique = ATTACK_TECHNIQUES.get(technique_id)
            if technique:
                matched.append(technique)
                seen.add(technique_id)

    return matched
