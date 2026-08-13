"""NVD 2.0 API client for CVE search, trending and detail lookups.

All responses are normalized into a compact internal shape consumed by the
threat intel service. Results are cached in-process to respect the NVD
rate limits (5 unauthenticated requests / 30 seconds).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from typing import Any

from app.core.config import settings
from app.integrations.threat_intel.cache import TTLCache
from app.logger import logger

_cache = TTLCache()

_last_success = True


def is_healthy() -> bool:
    """Whether the most recent NVD interaction succeeded."""

    return _last_success

_SESSION = requests.Session()
_retries = Retry(
    total=3,
    connect=2,
    read=2,
    backoff_factor=0.8,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=frozenset({"GET"}),
)
_SESSION.mount("https://", HTTPAdapter(max_retries=_retries))
_SESSION.mount("http://", HTTPAdapter(max_retries=_retries))


def _base_url() -> str:
    url = settings.THREAT_INTEL_NVD_API_URL or (
        "https://services.nvd.nist.gov/rest/json/cves/2.0"
    )
    return url.rstrip("/")


def _timeout() -> int:
    return settings.THREAT_INTEL_TIMEOUT_SECONDS


def _cve_list(payload: dict) -> list[dict]:
    vulnerabilities = payload.get("vulnerabilities") or []
    return vulnerabilities if isinstance(vulnerabilities, list) else []


def _fetch(
    params: dict[str, Any],
    *,
    start_index: int = 0,
) -> list[dict]:
    """Fetch one page of NVD results using `startIndex` pagination."""

    global _last_success

    page_params = dict(params)
    page_params["startIndex"] = start_index

    try:
        response = _SESSION.get(
            _base_url(),
            params=page_params,
            timeout=_timeout(),
        )
        response.raise_for_status()
        _last_success = True
        return _cve_list(response.json())
    except (requests.exceptions.RequestException, ValueError):
        _last_success = False
        raise


def _severity_from_score(score: float | None) -> str:
    if score is None:
        return "UNKNOWN"
    if score >= 9.0:
        return "CRITICAL"
    if score >= 7.0:
        return "HIGH"
    if score >= 4.0:
        return "MEDIUM"
    return "LOW"


def _extract_cvss(cve: dict) -> tuple[float | None, str]:
    metrics = cve.get("metrics") or {}
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        metric = metrics.get(key) or []
        if not metric:
            continue
        cvss = (metric[0].get("cvssData") or {})
        base_score = cvss.get("baseScore")
        if base_score is None:
            continue
        score = float(base_score)
        return score, _severity_from_score(score)

    return None, "UNKNOWN"


def _extract_cwes(cve: dict) -> list[str]:
    weaknesses = cve.get("weaknesses") or []
    cwes: list[str] = []
    for weakness in weaknesses:
        for description in weakness.get("description") or []:
            value = (description.get("value") or "").strip().upper()
            if value.startswith("CWE-"):
                cwes.append(value)
    return list(dict.fromkeys(cwes))


def _extract_affected(cve: dict) -> tuple[list[str], list[str]]:
    """Extract unique CPE vendor and product names from NVD configurations."""
    configurations = cve.get("configurations") or []
    vendors: list[str] = []
    products: list[str] = []
    for configuration in configurations:
        for node in configuration.get("nodes") or []:
            for match in node.get("cpeMatch") or []:
                cpe = (match.get("criteria") or "").split(":")
                if len(cpe) >= 4 and cpe[3] != "*":
                    vendors.append(cpe[3])
                if len(cpe) >= 5 and cpe[4] != "*":
                    products.append(cpe[4])
    return list(dict.fromkeys(vendors)), list(dict.fromkeys(products))


def _extract_references(cve: dict) -> list[dict]:
    references = cve.get("references") or []
    return [
        {
            "url": reference.get("url", ""),
            "source": reference.get("source", ""),
            "tags": reference.get("tags") or [],
        }
        for reference in references
        if reference.get("url")
    ]


def _short_title(description: str) -> str:
    first_sentence = description.split(".", 1)[0].strip()
    return first_sentence[:140] if first_sentence else "Vulnerability"


def _normalize_entry(entry: dict) -> dict:
    cve = entry.get("cve") or {}
    cve_id = (cve.get("id") or "").upper()

    descriptions = cve.get("descriptions") or []
    description = next(
        (
            desc.get("value", "")
            for desc in descriptions
            if desc.get("lang") == "en"
        ),
        "",
    )

    cvss_score, severity = _extract_cvss(cve)
    vendors, products = _extract_affected(cve)

    return {
        "id": cve_id,
        "title": _short_title(description) if description else cve_id,
        "description": description,
        "severity": severity,
        "cvss_score": cvss_score,
        "published": cve.get("published"),
        "last_modified": cve.get("lastModified"),
        "vendor": vendors[0] if vendors else None,
        "affected_vendors": vendors,
        "affected_products": products,
        "cwes": _extract_cwes(cve),
        "references": _extract_references(cve),
    }


def _normalize(entries: list[dict]) -> list[dict]:
    return [_normalize_entry(entry) for entry in entries]


def search_cves(
    query: str | None = None,
    severity: str | None = None,
    year: int | None = None,
    days: int | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search NVD by keyword, CVSS severity, year or recency window.

    `days` bounds results to a look-back window from now; `year` bounds to
    a calendar year. Both translate into `pubStartDate` / `pubEndDate`
    parameters understood by the NVD 2.0 API.
    """

    limit = max(1, min(limit, settings.THREAT_INTEL_MAX_RESULTS))

    params: dict[str, Any] = {"resultsPerPage": limit}

    if query:
        params["keywordSearch"] = query.strip()

    if severity:
        severity = severity.strip().upper()
        if severity in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
            params["cvssV3Severity"] = severity

    now = datetime.now(UTC)

    if days:
        start = (now - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00.000")
        params["pubStartDate"] = start
        params["pubEndDate"] = now.strftime("%Y-%m-%dT23:59:59.999")

    if year:
        params["pubStartDate"] = f"{year}-01-01T00:00:00.000"
        params["pubEndDate"] = f"{year}-12-31T23:59:59.999"

    cache_key = f"search:{sorted(params.items())}:{limit}"

    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        entries = _fetch(params)
    except (requests.exceptions.RequestException, ValueError):
        logger.warning("[NVD] Search failed", exc_info=True)
        entries = []

    results = _normalize(entries)
    _cache.set(cache_key, results)

    return results


def get_cve(cve_id: str) -> dict | None:
    """Fetch and normalize a single CVE by id, or None when unknown."""

    cve_id = cve_id.strip().upper()

    cache_key = f"cve:{cve_id}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    global _last_success

    try:
        response = _SESSION.get(
            _base_url(),
            params={
                "cveId": cve_id,
                "resultsPerPage": 1,
            },
            timeout=_timeout(),
        )
        response.raise_for_status()
        _last_success = True
        payload = _cve_list(response.json())
    except (requests.exceptions.RequestException, ValueError):
        _last_success = False
        logger.warning("[NVD] Lookup failed for %s", cve_id, exc_info=True)
        return None

    normalized = _normalize(payload)
    result = normalized[0] if normalized else None
    _cache.set(cache_key, result)

    return result
