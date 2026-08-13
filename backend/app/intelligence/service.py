"""
Service layer for the Threat Intelligence platform.

Implements the search workflow:

1. Validate the submitted value and auto-detect its IOC type.
2. Resolve the user's encrypted VirusTotal API key (never exposed).
3. Query the provider (24-hour cached, rate-limited, retried transport).
4. Compute risk / threat-tier metadata.
5. Persist a compact search-history record.
6. Return the normalized report to the client.

Failures are raised as ``GuardianXError`` subclasses (``ValidationError`` for
bad input, ``VirusTotalError`` subclasses for transport problems) so the
shared exception handlers in ``app.main`` map them to stable HTTP responses.
"""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.core.network import validate_domain_target
from app.services.activity_service import record_activity
from app.intelligence.providers import virustotal as virustotal_provider
from app.intelligence.schemas import (
    IntelligenceHistoryItem,
    IntelligenceHistoryResponse,
    IntelligenceLookupResponse,
    IntelligenceStatus,
    IOCType,
    ThreatIntelligenceReport,
)
from app.integrations.virustotal.exceptions import VirusTotalNotConfiguredError
from app.logger import logger
from app.models.intelligence_search import IntelligenceSearch
from app.services.integration_credentials import (
    get_api_key,
    get_credential,
)

_SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")


# ---------------------------------------------------------------------
# IOC detection
# ---------------------------------------------------------------------


def detect_ioc_type(value: str) -> IOCType:
    """
    Determine the indicator type of a raw search value.

    Detection order: http(s) URL, SHA256 hash, IP address, then hostname.
    Raises ``ValidationError`` when the value matches no known IOC shape.
    """
    value = value.strip()

    if not value:
        raise ValidationError("Provide an indicator to look up.")

    try:
        parsed = urlparse(value)
    except ValueError:
        parsed = None

    if parsed is not None and parsed.scheme in ("http", "https") and parsed.netloc:
        return IOCType.URL

    if _SHA256_RE.fullmatch(value):
        return IOCType.HASH

    try:
        ipaddress.ip_address(value)
        return IOCType.IP
    except ValueError:
        pass

    if _is_valid_hostname(value):
        return IOCType.DOMAIN

    raise ValidationError(
        "Unable to detect the indicator type. Provide a valid IP address, "
        "domain, http(s) URL or SHA256 hash."
    )


def _is_valid_hostname(value: str) -> bool:
    """Return whether the value is a plain DNS hostname."""
    try:
        validate_domain_target(value)
        return True
    except ValidationError:
        return False


# ---------------------------------------------------------------------
# Search history
# ---------------------------------------------------------------------


def _to_history_item(row: IntelligenceSearch) -> IntelligenceHistoryItem:
    return IntelligenceHistoryItem(
        id=row.id,
        resource_type=IOCType(row.resource_type),
        resource=row.resource,
        threat_level=row.threat_level,
        risk_score=row.risk_score,
        reputation=row.reputation,
        detected=row.detected,
        malicious=row.malicious,
        suspicious=row.suspicious,
        harmless=row.harmless,
        undetected=row.undetected,
        detection_ratio=row.detection_ratio,
        threat_category=row.threat_category,
        created_at=row.created_at,
    )


def _record_history(
    db: Session,
    user_id: int,
    report: ThreatIntelligenceReport,
) -> int:
    row = IntelligenceSearch(
        user_id=user_id,
        resource_type=report.resource_type.value,
        resource=report.resource,
        threat_level=report.threat_level.value,
        risk_score=report.risk_score,
        reputation=report.reputation,
        detected=report.detected,
        malicious=report.malicious,
        suspicious=report.suspicious,
        harmless=report.harmless,
        undetected=report.undetected,
        detection_ratio=report.detection_ratio,
        threat_category=report.threat_category,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row.id


def list_history(
    db: Session,
    user_id: int,
    *,
    ioc_type: IOCType | None = None,
    query: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> IntelligenceHistoryResponse:
    """Return a page of the user's search history, newest first."""
    q = db.query(IntelligenceSearch).filter(IntelligenceSearch.user_id == user_id)

    if ioc_type is not None:
        q = q.filter(IntelligenceSearch.resource_type == ioc_type.value)

    if query:
        q = q.filter(IntelligenceSearch.resource.ilike(f"%{query.strip()}%"))

    total = q.count()

    offset = max(0, (page - 1) * limit)
    rows = (
        q.order_by(IntelligenceSearch.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return IntelligenceHistoryResponse(
        items=[_to_history_item(row) for row in rows],
        total=total,
        page=page,
        limit=limit,
    )


def delete_history(db: Session, user_id: int, history_id: int) -> bool:
    """Delete a single history entry, scoped to the owning user."""
    row = (
        db.query(IntelligenceSearch)
        .filter(
            IntelligenceSearch.id == history_id,
            IntelligenceSearch.user_id == user_id,
        )
        .first()
    )

    if row is None:
        return False

    db.delete(row)
    db.commit()
    return True


def clear_history(db: Session, user_id: int) -> int:
    """Delete every history entry for the user. Returns the row count."""
    result = (
        db.query(IntelligenceSearch)
        .filter(IntelligenceSearch.user_id == user_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return int(result)


# ---------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------


def lookup(db: Session, user_id: int, value: str) -> IntelligenceLookupResponse:
    """
    Run the full IOC search workflow and persist the search history entry.
    """
    ioc_type = detect_ioc_type(value)

    api_key = get_api_key(db, user_id, "virustotal")
    if api_key is None:
        raise VirusTotalNotConfiguredError()

    report = virustotal_provider.lookup(api_key, ioc_type, value)

    logger.info(
        "[INTELLIGENCE] Lookup user=%s type=%s value=%s found=%s risk=%s",
        user_id,
        ioc_type.value,
        report.resource,
        report.found,
        report.risk_score,
    )

    history_id = _record_history(db, user_id, report)

    record_activity(
        db,
        user_id=user_id,
        action="intelligence_search",
        entity_type="ioc",
        detail=f"Threat intelligence lookup for {report.resource}",
        meta={"ioc_type": ioc_type.value, "found": report.found},
    )

    if report.found and report.malicious > 0:
        from app.services.alert_service import notify_malicious_ioc_alert

        notify_malicious_ioc_alert(
            db,
            user_id,
            value=report.resource,
            malicious_count=report.malicious,
            risk_score=report.risk_score,
        )

    db.commit()

    return IntelligenceLookupResponse(report=report, history_id=history_id)


def status(db: Session, user_id: int) -> IntelligenceStatus:
    """Whether the VirusTotal provider is configured for this user."""
    credential = get_credential(db, user_id, "virustotal")
    return IntelligenceStatus(
        provider="virustotal",
        configured=credential is not None,
    )
