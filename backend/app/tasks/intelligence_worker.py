"""Non-blocking CVE enrichment for finding detail views.

The worker deliberately stores only normalized intelligence in a bounded
in-memory cache. Source clients retain their own TTL caches, so a finding can
be opened repeatedly without generating duplicate NVD, KEV, or EPSS traffic.
"""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from threading import Lock

from app.integrations.threat_intel.cache import TTLCache
from app.integrations.threat_intel.service import get_cve_detail
from app.logger import logger

_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="cve-intel")
_cache = TTLCache(ttl_seconds=3600, max_entries=1024)
_pending: dict[str, Future[dict]] = {}
_lock = Lock()


def get_or_schedule(cve_id: str) -> tuple[str, dict | None]:
    """Return cached enrichment or schedule it and immediately report pending."""
    normalized = cve_id.strip().upper()
    cached = _cache.get(normalized)
    if cached is not None:
        return "ready", cached

    with _lock:
        future = _pending.get(normalized)
        if future is None:
            future = _executor.submit(get_cve_detail, normalized)
            _pending[normalized] = future

    if not future.done():
        return "pending", None

    with _lock:
        _pending.pop(normalized, None)
    try:
        result = future.result()
    except Exception:
        logger.warning("[INTELLIGENCE] Background enrichment failed for %s", normalized, exc_info=True)
        return "unavailable", None

    _cache.set(normalized, result)
    return "ready", result


def shutdown() -> None:
    """Stop worker threads during application shutdown."""
    _executor.shutdown(wait=False, cancel_futures=True)
