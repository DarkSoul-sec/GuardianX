"""FIRST EPSS (Exploit Prediction Scoring System) client.

The EPSS API accepts comma-separated CVE lists; lookups are batched up to
100 ids per request to stay within the API limits. Results are never cached
long-term because EPSS scores update daily.
"""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from app.core.config import settings
from app.logger import logger

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

_BATCH_SIZE = 100

_last_success = True


def is_healthy() -> bool:
    """Whether the most recent EPSS batch lookup succeeded."""

    return _last_success


def _api_url() -> str:
    return settings.THREAT_INTEL_EPSS_API_URL or "https://api.first.org/data/v1/epss"


def _chunks(values: list[str], size: int):
    for index in range(0, len(values), size):
        yield values[index : index + size]


def _fetch_batch(cve_ids: list[str]) -> dict[str, dict]:
    global _last_success

    response = _SESSION.get(
        _api_url(),
        params={"cve": ",".join(cve_ids)},
        timeout=settings.THREAT_INTEL_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    _last_success = True

    payload = response.json()
    results: dict[str, dict] = {}

    for item in payload.get("data") or []:
        cve_id = item.get("cve")
        if not cve_id:
            continue
        try:
            score = round(float(item.get("epss", 0)), 4)
            percentile = round(float(item.get("percentile", 0)) * 100, 1)
        except (TypeError, ValueError):
            continue
        results[cve_id.upper()] = {
            "score": score,
            "percentile": percentile,
        }

    return results


def get_epss_scores(cve_ids: list[str]) -> dict[str, dict]:
    """Return {CVE_ID: {score, percentile}} for every provided CVE.

    Missing ids (not yet scored by FIRST) are simply absent from the result.
    A failed batch degrades to an empty mapping for that batch rather than
    failing the whole enrichment.
    """

    unique = list(dict.fromkeys(
        cve_id.strip().upper() for cve_id in cve_ids if cve_id
    ))
    if not unique:
        return {}

    global _last_success

    merged: dict[str, dict] = {}

    for batch in _chunks(unique, _BATCH_SIZE):
        try:
            merged.update(_fetch_batch(batch))
        except (requests.exceptions.RequestException, ValueError):
            _last_success = False
            logger.warning("[EPSS] Batch lookup failed", exc_info=True)

    return merged
