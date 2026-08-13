"""
HTTP transport for the VirusTotal v3 API.

Handles request construction, per-key auth, manual retries with exponential
backoff, client-side rate limiting and JSON parsing. The public surface is
``_get(api_key, path)`` which returns the decoded JSON body for a GET
request, ``None`` for a 404, and raises ``VirusTotalError`` subclasses for
every other failure so callers never touch ``requests`` directly.

API keys are passed per call — the transport never reads keys from
configuration or storage — so every user's quota is throttled independently.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from app.core.config import settings
from app.integrations.virustotal.exceptions import (
    VirusTotalError,
    VirusTotalInvalidKeyError,
    VirusTotalRateLimitError,
)

_STATUS_FORCELIST = frozenset({429, 500, 502, 503, 504})


class _PerKeyTokenBucket:
    """
    A token bucket per API key so one user's burst cannot starve another.

    The bucket size is small (free tier) to protect the shared quota of every
    BYOAPI key. Entries are evicted least-recently-used so the map cannot grow
    without bound as keys are added and removed.
    """

    def __init__(
        self,
        capacity: float,
        refill_per_second: float,
        max_keys: int = 128,
    ) -> None:
        self._capacity = capacity
        self._refill_per_second = refill_per_second
        self._max_keys = max_keys
        self._buckets: "OrderedDict[str, tuple[float, float]]" = OrderedDict()
        self._lock = threading.Lock()

    def acquire(self, key: str) -> None:
        while True:
            with self._lock:
                tokens, refilled = self._buckets.get(
                    key,
                    (self._capacity, time.monotonic()),
                )

                now = time.monotonic()
                tokens = min(
                    self._capacity,
                    tokens + (now - refilled) * self._refill_per_second,
                )

                if tokens >= 1.0:
                    tokens -= 1.0
                    self._buckets.pop(key, None)
                    self._buckets[key] = (tokens, now)

                    while len(self._buckets) > self._max_keys:
                        self._buckets.popitem(last=False)

                    return

                wait = (1.0 - tokens) / self._refill_per_second

            time.sleep(max(wait, 0.05))


_BUCKET = _PerKeyTokenBucket(
    capacity=max(float(settings.VIRUSTOTAL_RATE_LIMIT_PER_MINUTE), 1.0),
    refill_per_second=max(settings.VIRUSTOTAL_RATE_LIMIT_PER_MINUTE, 1) / 60.0,
)

# Connection pooling is kept via requests.Session. Retries on connect/read
# errors are handled by urllib3; HTTP status retries are handled manually so
# 429 responses can be surfaced distinctly (rate limit) when needed.
_SESSION = requests.Session()
_RETRIES = Retry(
    total=settings.VIRUSTOTAL_MAX_RETRIES,
    connect=settings.VIRUSTOTAL_MAX_RETRIES,
    read=settings.VIRUSTOTAL_MAX_RETRIES,
    backoff_factor=0.7,
    status=False,
    allowed_methods=frozenset({"GET"}),
)
_SESSION.mount("https://", HTTPAdapter(max_retries=_RETRIES))
_SESSION.mount("http://", HTTPAdapter(max_retries=_RETRIES))


def _retry_delay(response: requests.Response, attempt: int) -> float:
    """Backoff honouring VirusTotal's ``Retry-After`` header when present."""
    retry_after = response.headers.get("Retry-After")

    if retry_after:
        try:
            return max(float(retry_after), 0.1)
        except ValueError:
            pass

    return 0.7 * (2**attempt)


def _get(
    api_key: str,
    path: str,
    *,
    retries: int | None = None,
) -> dict[str, Any] | None:
    """GET a VirusTotal endpoint, returning parsed JSON or None on 404.

    ``retries`` overrides the configured retry budget; pass ``0`` for
    connection tests so rate-limit responses surface immediately instead of
    being retried.
    """
    if not api_key:
        raise VirusTotalError("A VirusTotal API key is required.")

    max_retries = (
        retries
        if retries is not None
        else settings.VIRUSTOTAL_MAX_RETRIES
    )

    _BUCKET.acquire(api_key)

    url = f"{settings.VIRUSTOTAL_API_URL.rstrip('/')}/{path.lstrip('/')}"

    response: requests.Response | None = None

    for attempt in range(max_retries + 1):
        try:
            response = _SESSION.get(
                url,
                headers={"x-apikey": api_key},
                timeout=settings.VIRUSTOTAL_TIMEOUT_SECONDS,
            )
        except requests.exceptions.RequestException as exc:
            if attempt < max_retries:
                time.sleep(0.7 * (2**attempt))
                continue
            raise VirusTotalError(
                f"VirusTotal request to {path} failed: {exc}"
            ) from exc

        if response.status_code in _STATUS_FORCELIST and attempt < max_retries:
            time.sleep(_retry_delay(response, attempt))
            continue

        break

    if response is None:
        raise VirusTotalError(f"VirusTotal request to {path} failed.")

    if response.status_code in (401, 403):
        raise VirusTotalInvalidKeyError()

    if response.status_code == requests.codes.not_found:
        return None

    if response.status_code == 429:
        raise VirusTotalRateLimitError()

    if response.status_code >= 400:
        raise VirusTotalError(
            f"VirusTotal returned HTTP {response.status_code} for {path}: "
            f"{response.text[:300]}"
        )

    try:
        return response.json()
    except ValueError as exc:
        raise VirusTotalError(
            "VirusTotal returned an invalid JSON response."
        ) from exc
