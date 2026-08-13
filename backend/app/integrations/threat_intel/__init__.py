"""Threat Intelligence integration package.

Unifies NVD, CISA KEV, FIRST EPSS and MITRE ATT&CK behind a single,
bounded, cache-backed service layer. The package is provider-agnostic:
each source client is self-contained and the orchestration lives in
:mod:`app.integrations.threat_intel.service`.
"""

from __future__ import annotations

from app.integrations.threat_intel.service import (
    get_attack_techniques,
    get_cve_detail,
    get_kev_catalog,
    get_stats,
    get_trending,
    search_cves,
)

__all__ = [
    "get_attack_techniques",
    "get_cve_detail",
    "get_kev_catalog",
    "get_stats",
    "get_trending",
    "search_cves",
]
