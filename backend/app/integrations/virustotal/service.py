"""
Service layer for VirusTotal intelligence lookups and BYOAPI credentials.

Public functions fall into two groups:

- Credential management: store/remove/test the user's own VirusTotal API key.
  Keys are encrypted at rest by ``app.services.integration_credentials`` and
  never returned to callers.
- Intelligence lookups: validate the requested value, hit the cache, call the
  VirusTotal API through the transport in :mod:`client`, and normalize the raw
  report into :class:`VirusTotalLookupResponse`.

Validation errors raise ``app.core.exceptions.ValidationError`` (HTTP 400) and
transport failures are surfaced as ``VirusTotalError`` subclasses (HTTP
502/503) via the shared exception handlers.
"""

from __future__ import annotations

import base64
import ipaddress
import re
from datetime import UTC, datetime
from urllib.parse import quote, urlparse

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.core.network import validate_domain_target
from app.integrations.virustotal.cache import TTLCache
from app.integrations.virustotal.client import _get
from app.integrations.virustotal.exceptions import (
    VirusTotalError,
    VirusTotalInvalidKeyError,
    VirusTotalNotConfiguredError,
    VirusTotalRateLimitError,
)
from app.integrations.virustotal.models import Attributes, RawReport, VendorResult
from app.integrations.virustotal.schemas import (
    IntegrationStatus,
    VendorDetection,
    VirusTotalConnectionStatus,
    VirusTotalLookupResponse,
)
from app.services.integration_credentials import (
    delete_credential,
    get_api_key,
    get_credential,
    set_status,
    upsert_api_key,
)

_SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")

_PROVIDER = "virustotal"

_PERMALINK_TEMPLATES = {
    "url": "https://www.virustotal.com/gui/url/{value}",
    "domain": "https://www.virustotal.com/gui/domain/{value}",
    "ip": "https://www.virustotal.com/gui/ip-address/{value}",
    "file": "https://www.virustotal.com/gui/file/{value}",
}

# Lightweight, stable resource used to validate an API key without depending
# on a user-supplied value.
_TEST_RESOURCE = "ip_addresses/8.8.8.8"

_CACHE = TTLCache[VirusTotalLookupResponse](
    ttl_seconds=settings.VIRUSTOTAL_CACHE_TTL_SECONDS,
    max_entries=settings.VIRUSTOTAL_CACHE_MAX_ENTRIES,
)


# ---------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------


def _url_id(url: str) -> str:
    """URL-safe base64 identifier used by the VirusTotal API and web app."""
    return base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")


def _validate_url(value: str) -> str:
    value = value.strip()

    try:
        parsed = urlparse(value)
    except ValueError:
        parsed = None

    if parsed is None or parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValidationError("Provide a valid http(s) URL to look up.")

    return value


def _validate_ip(value: str) -> str:
    value = value.strip()

    try:
        ipaddress.ip_address(value)
    except ValueError:
        raise ValidationError("Provide a valid IPv4 or IPv6 address to look up.")

    return value


def _validate_sha256(value: str) -> str:
    value = value.strip().lower()

    if not _SHA256_RE.fullmatch(value):
        raise ValidationError("Provide a valid SHA256 hash (64 hex characters).")

    return value


def _validate_api_key(value: str) -> str:
    value = value.strip()

    if not value or len(value) < 32:
        raise ValidationError(
            "Provide a valid VirusTotal API key (it looks too short)."
        )

    return value


# ---------------------------------------------------------------------
# Credential management
# ---------------------------------------------------------------------


def get_configured_api_key(db: Session, user_id: int) -> str:
    """Return the user's decrypted API key or raise ``NotConfigured``."""
    api_key = get_api_key(db, user_id, _PROVIDER)

    if api_key is None:
        raise VirusTotalNotConfiguredError()

    return api_key


def get_optional_api_key(db: Session, user_id: int) -> str | None:
    """Return the user's decrypted API key, or ``None`` if not configured."""
    return get_api_key(db, user_id, _PROVIDER)


def test_connection(api_key: str) -> VirusTotalConnectionStatus:
    """
    Validate an API key with a lightweight VirusTotal request.

    ``retries=0`` ensures rate-limit and invalid-key responses surface
    immediately so the caller can give clear, instant feedback.
    """
    try:
        _get(api_key, _TEST_RESOURCE, retries=0)
    except VirusTotalInvalidKeyError:
        return VirusTotalConnectionStatus(
            status="invalid",
            message="Invalid API key — check your credentials.",
        )
    except VirusTotalRateLimitError:
        return VirusTotalConnectionStatus(
            status="rate_limited",
            message="Rate limit reached — you've exceeded the current quota.",
        )
    except VirusTotalError as exc:
        return VirusTotalConnectionStatus(
            status="unreachable",
            message=f"VirusTotal is unreachable — {exc.detail}",
        )

    return VirusTotalConnectionStatus(
        status="connected",
        message="Connected — API key is valid.",
    )


def connect_api_key(
    db: Session,
    user_id: int,
    api_key: str,
) -> IntegrationStatus:
    """
    Validate, encrypt and store a user's VirusTotal API key.

    The key is tested first so the persisted status is accurate from the very
    first save. The plaintext key is never written to the database.
    """
    api_key = _validate_api_key(api_key)

    result = test_connection(api_key)

    credential = upsert_api_key(
        db,
        user_id,
        _PROVIDER,
        api_key,
        status=result.status,
    )

    return _to_status(credential, result)


def test_stored_connection(db: Session, user_id: int) -> IntegrationStatus:
    """Re-test the stored API key (if any) and persist the outcome."""
    credential = get_credential(db, user_id, _PROVIDER)

    if credential is None:
        return IntegrationStatus(
            provider=_PROVIDER,
            configured=False,
            status="not_configured",
            message="Add your VirusTotal API key to get started.",
        )

    api_key = get_api_key(db, user_id, _PROVIDER)
    result = test_connection(api_key or "")

    credential = set_status(db, credential, result.status)
    return _to_status(credential, result)


def get_status(db: Session, user_id: int) -> IntegrationStatus:
    """Return the stored connection status for the user's VirusTotal key."""
    credential = get_credential(db, user_id, _PROVIDER)

    if credential is None:
        return IntegrationStatus(
            provider=_PROVIDER,
            configured=False,
            status="not_configured",
            message="Add your VirusTotal API key to get started.",
        )

    return _to_status(credential)


def disconnect_api_key(db: Session, user_id: int) -> bool:
    """Remove the user's stored VirusTotal API key."""
    return delete_credential(db, user_id, _PROVIDER)


def _to_status(
    credential,
    result: VirusTotalConnectionStatus | None = None,
) -> IntegrationStatus:
    """Build the public status envelope without ever exposing the key."""
    if result is not None:
        message = result.message
        status = result.status
    else:
        status = credential.status
        message = _STATUS_MESSAGES.get(status, "Unknown connection status.")

    return IntegrationStatus(
        provider=credential.provider,
        configured=True,
        status=status,
        message=message,
        last_tested_at=credential.last_tested_at,
        created_at=credential.created_at,
        updated_at=credential.updated_at,
    )


_STATUS_MESSAGES = {
    "connected": "Connected — API key is valid.",
    "invalid": "Invalid API key — check your credentials.",
    "rate_limited": "Rate limit reached — you've exceeded the current quota.",
    "unreachable": "VirusTotal is unreachable. Check your network connection.",
    "not_configured": "Add your VirusTotal API key to get started.",
}


# ---------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------


def _api_path(resource_type: str, resource: str) -> str:
    if resource_type == "url":
        return f"urls/{_url_id(resource)}"
    if resource_type == "domain":
        return f"domains/{quote(resource, safe='')}"
    if resource_type == "ip":
        return f"ip_addresses/{resource}"
    return f"files/{resource}"


def _permalink(resource_type: str, resource: str) -> str:
    value = _url_id(resource) if resource_type == "url" else resource
    return _PERMALINK_TEMPLATES[resource_type].format(value=value)


def _top_verdict(results: dict[str, VendorResult]) -> str | None:
    for item in results.values():
        if item.category in ("malicious", "suspicious") and item.result:
            return item.result
    for item in results.values():
        if item.category in ("malicious", "suspicious"):
            return item.category
    return None


def _threat_category(resource_type: str, attributes: Attributes) -> str | None:
    if resource_type == "file":
        if attributes.popular_threat_category:
            return attributes.popular_threat_category

        verdict = _top_verdict(attributes.last_analysis_results)
        if verdict:
            return verdict

        return attributes.type_description

    if attributes.categories:
        return next(iter(attributes.categories.values()))

    return _top_verdict(attributes.last_analysis_results)


def _to_response(
    resource_type: str,
    resource: str,
    report: RawReport,
) -> VirusTotalLookupResponse:
    attributes = report.data.attributes
    stats = attributes.last_analysis_stats

    malicious = stats.malicious if stats else 0
    suspicious = stats.suspicious if stats else 0
    undetected = stats.undetected if stats else 0
    harmless = stats.harmless if stats else 0
    timeout = stats.timeout if stats else 0
    total = (
        malicious
        + suspicious
        + undetected
        + harmless
        + timeout
        + (stats.confirmed_timeout if stats else 0)
        + (stats.failure if stats else 0)
        + (stats.type_unsupported if stats else 0)
    )

    vendor_detections = [
        VendorDetection(
            engine=name,
            category=item.category,
            result=item.result,
        )
        for name, item in attributes.last_analysis_results.items()
    ]

    reputation = attributes.reputation or 0

    last_analysis_date = None
    if attributes.last_analysis_date:
        last_analysis_date = datetime.fromtimestamp(
            attributes.last_analysis_date,
            tz=UTC,
        )

    return VirusTotalLookupResponse(
        resource_type=resource_type,
        resource=resource,
        permalink=_permalink(resource_type, resource),
        found=True,
        detected=malicious > 0 or suspicious > 0,
        malicious=malicious,
        suspicious=suspicious,
        undetected=undetected,
        harmless=harmless,
        timeout=timeout,
        total=total,
        detection_ratio=f"{malicious}/{total}",
        reputation=reputation,
        community_score=reputation,
        threat_category=_threat_category(resource_type, attributes),
        last_analysis_date=last_analysis_date,
        vendor_detections=vendor_detections,
    )


def _not_found(resource_type: str, resource: str) -> VirusTotalLookupResponse:
    return VirusTotalLookupResponse(
        resource_type=resource_type,
        resource=resource,
        permalink=_permalink(resource_type, resource),
        found=False,
    )


# ---------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------


def _lookup(
    api_key: str,
    resource_type: str,
    resource: str,
) -> VirusTotalLookupResponse:
    cache_key = f"{resource_type}:{resource}"

    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached

    raw = _get(api_key, _api_path(resource_type, resource))

    if raw is None:
        response = _not_found(resource_type, resource)
        _CACHE.set(cache_key, response)
        return response

    try:
        report = RawReport.model_validate(raw)
    except Exception as exc:  # pydantic.ValidationError
        raise VirusTotalError(
            "VirusTotal returned an unexpected response shape."
        ) from exc

    response = _to_response(resource_type, resource, report)
    _CACHE.set(cache_key, response)
    return response


def lookup_url(api_key: str, url: str) -> VirusTotalLookupResponse:
    """Return the VirusTotal reputation report for an http(s) URL."""
    return _lookup(api_key, "url", _validate_url(url))


def lookup_domain(api_key: str, domain: str) -> VirusTotalLookupResponse:
    """Return the VirusTotal reputation report for a domain."""
    return _lookup(api_key, "domain", validate_domain_target(domain))


def lookup_ip(api_key: str, ip: str) -> VirusTotalLookupResponse:
    """Return the VirusTotal reputation report for an IP address."""
    return _lookup(api_key, "ip", _validate_ip(ip))


def lookup_file_hash(api_key: str, sha256: str) -> VirusTotalLookupResponse:
    """Return the VirusTotal reputation report for a SHA256 file hash."""
    return _lookup(api_key, "file", _validate_sha256(sha256))
