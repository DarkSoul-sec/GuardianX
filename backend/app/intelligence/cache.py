"""
In-process 24-hour cache for Threat Intelligence reports.

The cache reuses the thread-safe bounded :class:`TTLCache` from the VirusTotal
integration so no cache logic is duplicated. Reports are cached per
``{ioc_type}:{normalized_value}`` and served for
``INTELLIGENCE_CACHE_TTL_SECONDS`` (default 24 hours) to keep lookups within
BYOAPI quotas. ``None`` is never a stored value, so a miss is unambiguous.
"""

from __future__ import annotations

from app.core.config import settings
from app.integrations.virustotal.cache import TTLCache
from app.intelligence.schemas import ThreatIntelligenceReport

intelligence_cache: TTLCache[ThreatIntelligenceReport] = TTLCache(
    ttl_seconds=settings.INTELLIGENCE_CACHE_TTL_SECONDS,
    max_entries=settings.INTELLIGENCE_CACHE_MAX_ENTRIES,
)


def cache_key(ioc_type: str, value: str) -> str:
    """Build the normalized cache key for an IOC."""
    return f"{ioc_type}:{value.strip().lower()}"


def get_cached(key: str) -> ThreatIntelligenceReport | None:
    """Return a cached report, or ``None`` on a miss."""
    return intelligence_cache.get(key)


def set_cached(key: str, report: ThreatIntelligenceReport) -> None:
    """Store a report in the cache."""
    intelligence_cache.set(key, report)


def clear_cache() -> None:
    """Drop all cached reports (used by tests and admin tooling)."""
    intelligence_cache.clear()
