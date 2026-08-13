import threading
import time

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from typing import List, Dict, Any

from app.logger import logger

NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

# Cap the number of CVEs fetched per lookup so an over-broad CPE match
# cannot balloon into a huge response or a database write storm.
NVD_RESULTS_PER_PAGE = 200

_CACHE_TTL_SECONDS = 3600
_CACHE_MAX_ENTRIES = 512
_CACHE_LOCK = threading.Lock()
_CACHE: Dict[str, tuple[float, List[Dict[str, Any]]]] = {}

_SESSION = requests.Session()
_retries = Retry(
    total=3,
    connect=3,
    read=3,
    backoff_factor=0.8,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=frozenset({"GET"}),
)
_SESSION.mount("https://", HTTPAdapter(max_retries=_retries))
_SESSION.mount("http://", HTTPAdapter(max_retries=_retries))


def _cache_get(key: str) -> List[Dict[str, Any]] | None:
    with _CACHE_LOCK:
        entry = _CACHE.get(key)

    if entry is None:
        return None

    expires_at, value = entry

    if time.monotonic() > expires_at:
        return None

    return value


def _cache_set(key: str, value: List[Dict[str, Any]]) -> None:
    with _CACHE_LOCK:
        if len(_CACHE) >= _CACHE_MAX_ENTRIES and key not in _CACHE:
            _CACHE.clear()

        _CACHE[key] = (
            time.monotonic() + _CACHE_TTL_SECONDS,
            value,
        )


def _extract_product_keyword(cpe: str) -> str:
    """
    Extract a product keyword from a CPE string for use in keyword search.
    """
    parts = cpe.split(":")

    if len(parts) < 6:
        return ""

    product = parts[4].strip().lower()
    vendor = parts[3].strip().lower()

    if product and product != "*":
        return product

    if vendor and vendor != "*":
        return vendor

    return ""


def _parse_vulnerabilities(data: dict) -> List[Dict[str, Any]]:
    vulnerabilities = data.get("vulnerabilities", [])

    if not isinstance(vulnerabilities, list):
        return []

    return vulnerabilities[:NVD_RESULTS_PER_PAGE]


def _fetch_vulnerabilities_for_cpe(cpe: str) -> List[Dict[str, Any]]:
    """
    Query NVD using the cpeName endpoint.
    """
    response = _SESSION.get(
        NVD_API_URL,
        params={
            "cpeName": cpe,
            "resultsPerPage": NVD_RESULTS_PER_PAGE,
        },
        timeout=15,
    )
    response.raise_for_status()

    return _parse_vulnerabilities(response.json())


def _fetch_vulnerabilities_by_keyword(keyword: str) -> List[Dict[str, Any]]:
    """
    Fallback to NVD keyword search when the CPE cannot be used directly.
    """
    response = _SESSION.get(
        NVD_API_URL,
        params={
            "keywordSearch": keyword,
            "resultsPerPage": NVD_RESULTS_PER_PAGE,
        },
        timeout=15,
    )
    response.raise_for_status()

    return _parse_vulnerabilities(response.json())


def get_cves_by_cpe(cpe: str | None) -> List[Dict[str, Any]]:
    """
    Fetch all vulnerabilities matching a CPE from the NVD API.

    Results are cached in-process for an hour to keep repeated scans and
    multiple assets sharing a CPE from hammering the NVD API. When the CPE
    is versionless or wildcarded, the NVD `cpeName` endpoint may reject it,
    in which case we fall back to a keyword search using the product name
    extracted from the CPE.
    """

    if not cpe:
        return []

    cpe = cpe.strip()

    if not cpe.startswith("cpe:2.3:"):
        logger.warning("[NVD] Invalid CPE format: %s", cpe)
        return []

    parts = cpe.split(":")

    if len(parts) < 6:
        logger.warning(
            "[NVD] Invalid CPE shape: expected at least 6 parts, got %s for %s",
            len(parts),
            cpe,
        )
        return []

    cache_key = f"cpe:{cpe}"

    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    keyword = _extract_product_keyword(cpe)

    try:
        vulnerabilities = _fetch_vulnerabilities_for_cpe(cpe)
    except requests.exceptions.HTTPError as e:
        logger.warning("[NVD] HTTP Error: %s", e)
        vulnerabilities = None
    except requests.exceptions.ConnectionError as e:
        logger.warning("[NVD] Connection Error: %s", e)
        vulnerabilities = None
    except requests.exceptions.Timeout as e:
        logger.warning("[NVD] Request Timed Out: %s", e)
        vulnerabilities = None
    except requests.exceptions.RequestException as e:
        logger.warning("[NVD] Request Failed: %s", e)
        vulnerabilities = None
    except ValueError:
        logger.warning("[NVD] Failed to parse JSON response.")
        vulnerabilities = None

    if vulnerabilities is None and keyword:
        logger.info("[NVD] Falling back to keyword search for: %s", keyword)
        try:
            vulnerabilities = _fetch_vulnerabilities_by_keyword(keyword)
        except requests.exceptions.HTTPError as e:
            logger.warning("[NVD] Keyword fallback HTTP Error: %s", e)
        except requests.exceptions.ConnectionError as e:
            logger.warning("[NVD] Keyword fallback Connection Error: %s", e)
        except requests.exceptions.Timeout as e:
            logger.warning("[NVD] Keyword fallback Request Timed Out: %s", e)
        except requests.exceptions.RequestException as e:
            logger.warning("[NVD] Keyword fallback Request Failed: %s", e)
        except ValueError:
            logger.warning("[NVD] Keyword fallback failed to parse JSON response.")

    if vulnerabilities is None:
        vulnerabilities = []

    _cache_set(cache_key, vulnerabilities)

    return vulnerabilities
