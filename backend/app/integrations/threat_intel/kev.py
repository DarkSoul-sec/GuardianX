"""CISA Known Exploited Vulnerabilities (KEV) catalog client.

The full catalog is fetched once and cached; membership and enrichment are
performed against the cached snapshot so per-CVE lookups never hit the feed.
"""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from app.core.config import settings
from app.integrations.threat_intel.cache import TTLCache
from app.logger import logger

_cache = TTLCache(ttl_seconds=1800, max_entries=64)

_last_success = True


def is_healthy() -> bool:
    """Whether the most recent KEV catalog fetch succeeded."""

    return _last_success

_SESSION = requests.Session()
_retries = Retry(
    total=2,
    connect=2,
    read=2,
    backoff_factor=0.8,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=frozenset({"GET"}),
)
_SESSION.mount("https://", HTTPAdapter(max_retries=_retries))
_SESSION.mount("http://", HTTPAdapter(max_retries=_retries))


def _catalog_url() -> str:
    return settings.THREAT_INTEL_KEV_API_URL or (
        "https://www.cisa.gov/sites/default/files/feeds/"
        "known_exploited_vulnerabilities.json"
    )


def _normalize(entry: dict) -> dict:
    return {
        "cve_id": (entry.get("cveID") or "").upper(),
        "vendor": entry.get("vendorProject") or "",
        "product": entry.get("product") or "",
        "vulnerability_name": entry.get("vulnerabilityName") or "",
        "description": entry.get("shortDescription") or "",
        "required_action": entry.get("requiredAction") or "",
        "due_date": entry.get("dueDate"),
        "date_added": entry.get("dateAdded"),
        "known_ransomware_campaign": bool(
            entry.get("knownRansomwareCampaignUse") or False
        ),
        "notes": entry.get("notes"),
    }


def _fetch_catalog() -> list[dict]:
    global _last_success

    response = _SESSION.get(
        _catalog_url(),
        timeout=settings.THREAT_INTEL_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    _last_success = True

    payload = response.json()
    vulnerabilities = payload.get("vulnerabilities") or []
    return [_normalize(entry) for entry in vulnerabilities]


def get_kev_catalog() -> list[dict]:
    """Return the KEV catalog (cached), degraded to an empty list on failure."""

    global _last_success

    cached = _cache.get("kev")
    if cached is not None:
        return cached

    try:
        catalog = _fetch_catalog()
    except (requests.exceptions.RequestException, ValueError):
        _last_success = False
        logger.warning("[KEV] Catalog fetch failed", exc_info=True)
        catalog = []

    _cache.set("kev", catalog)
    return catalog


def get_kev_entry(cve_id: str) -> dict | None:
    """Return the KEV record for a CVE, or None when not actively exploited."""

    needle = cve_id.strip().upper()

    for entry in get_kev_catalog():
        if entry["cve_id"] == needle:
            return entry

    return None


def is_exploited(cve_id: str) -> bool:
    return get_kev_entry(cve_id) is not None
