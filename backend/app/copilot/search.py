"""
Natural-language to GuardianX query translation.

Turns plain-English questions such as "Show my critical vulnerabilities" or
"Assets running PostgreSQL" into structured, ownership-scoped database
queries. The same structured result set is rendered by the rules provider and
embedded in the prompt for LLM providers, so both paths stay consistent.

Every query is scoped through :func:`apply_asset_scope` — Copilot never
returns data from outside the requesting user's estate.
"""

from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.copilot.intents import extract_cve
from app.models.asset import Asset
from app.models.finding import Finding
from app.models.scan import Scan
from app.models.scan_result import ScanResult
from app.models.user import User
from app.services.query_helpers import apply_asset_scope

_SEVERITY_KEYWORDS = (
    ("CRITICAL", ("critical", "emergency")),
    ("HIGH", ("high", "urgent")),
    ("MEDIUM", ("medium", "moderate")),
    ("LOW", ("low", "minor")),
)

_SERVICE_KEYWORDS = (
    ("ssh", ("ssh", "secure shell")),
    ("postgresql", ("postgres", "postgresql")),
    ("mysql", ("mysql", "mariadb")),
    ("redis", ("redis",)),
    ("mongodb", ("mongo", "mongodb")),
    ("http", ("http", "https", "web server", "web", "iis", "apache", "nginx")),
    ("ftp", ("ftp", "sftp", "ftps")),
    ("smtp", ("smtp", "imap", "pop3", "mail")),
    ("rdp", ("rdp", "remote desktop")),
    ("smtp", ("smtp",)),
    ("ldap", ("ldap", "active directory")),
    ("dns", ("dns",)),
    ("telnet", ("telnet",)),
    ("database", ("database", "oracle", "sql server", "db")),
    ("docker", ("docker", "container")),
    ("kafka", ("kafka", "rabbitmq", "memcached")),
)

_ASSET_TYPE_KEYWORDS = (
    ("WEBSITE", ("website", "web site", "web application")),
    ("SERVER", ("server", "host")),
    ("WORKSTATION", ("workstation", "desktop", "laptop")),
    ("API", ("api", "rest api")),
    ("CLOUD", ("cloud",)),
    ("DATABASE", ("database", "db server")),
)

_SERVICE_HINTS = tuple(
    keyword
    for _name, keywords in _SERVICE_KEYWORDS
    for keyword in keywords
)

_PORT_PATTERN = re.compile(
    r"\bport\s*:?\s*(\d{1,5})\b|\b(?:tcp|udp)\/(\d{1,5})\b"
)


def _parse_severity(text: str) -> str | None:
    for severity, keywords in _SEVERITY_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            return severity
    return None


def _parse_service(text: str) -> str | None:
    for name, keywords in _SERVICE_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            return name
    return None


def _parse_port(text: str) -> int | None:
    match = _PORT_PATTERN.search(text)
    if match:
        return int(match.group(1) or match.group(2))
    return None


def _parse_asset_type(text: str) -> str | None:
    for asset_type, keywords in _ASSET_TYPE_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            return asset_type
    return None


def _query_findings(
    db: Session,
    current_user: User,
    *,
    severity: str | None,
    service: str | None,
    port: int | None,
    cve: str | None,
    limit: int = 20,
) -> list[dict]:
    query = (
        db.query(
            Finding.id,
            Finding.title,
            Finding.severity,
            Finding.cve,
            Finding.cvss,
            Finding.status,
            Asset.name.label("asset_name"),
            ScanResult.service.label("service"),
        )
        .join(ScanResult, Finding.scan_result_id == ScanResult.id)
        .join(Scan, ScanResult.scan_id == Scan.id)
        .join(Asset, Scan.asset_id == Asset.id)
    )

    if severity:
        query = query.filter(Finding.severity == severity)

    if service:
        query = query.filter(ScanResult.service.ilike(f"%{service}%"))

    if port:
        query = query.filter(ScanResult.port == port)

    if cve:
        query = query.filter(Finding.cve.ilike(f"%{cve}%"))

    rows = (
        apply_asset_scope(query, current_user)
        .order_by(Finding.cvss.desc().nullslast())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": row.id,
            "title": row.title,
            "severity": row.severity,
            "cve": row.cve,
            "cvss": row.cvss,
            "status": row.status,
            "asset": row.asset_name,
            "service": row.service,
        }
        for row in rows
    ]


def _query_assets(
    db: Session,
    current_user: User,
    *,
    asset_type: str | None,
    service: str | None,
    port: int | None,
    exposed: bool,
    limit: int = 20,
) -> list[dict]:
    matching_ids = (
        db.query(Scan.asset_id)
        .join(ScanResult, ScanResult.scan_id == Scan.id)
        .filter(ScanResult.state == "open")
    )

    if service:
        matching_ids = matching_ids.filter(
            ScanResult.service.ilike(f"%{service}%")
        )

    if port:
        matching_ids = matching_ids.filter(ScanResult.port == port)

    matching_ids = matching_ids.distinct().subquery()

    query = (
        db.query(
            Asset.id,
            Asset.name,
            Asset.asset_type,
            Asset.ip_address,
            Asset.domain,
            Asset.criticality,
        )
        .filter(
            Asset.id.in_(db.query(matching_ids.c.asset_id)),
        )
    )

    if asset_type:
        query = query.filter(Asset.asset_type == asset_type)

    if exposed:
        query = query.filter(Asset.ip_address.is_not(None))

    query = apply_asset_scope(query, current_user)
    query = query.limit(limit)

    rows = query.all()

    return [
        {
            "id": row.id,
            "name": row.name,
            "asset_type": (
                row.asset_type.value
                if hasattr(row.asset_type, "value")
                else str(row.asset_type)
            ),
            "ip_address": row.ip_address,
            "domain": row.domain,
            "criticality": row.criticality,
        }
        for row in rows
    ]


def _query_services(
    db: Session,
    current_user: User,
    *,
    service: str | None,
    port: int | None,
    limit: int = 20,
) -> list[dict]:
    query = (
        db.query(
            ScanResult.port,
            ScanResult.protocol,
            ScanResult.service,
            ScanResult.product,
            ScanResult.version,
            Asset.name.label("asset_name"),
        )
        .join(Scan, ScanResult.scan_id == Scan.id)
        .join(Asset, Scan.asset_id == Asset.id)
        .filter(ScanResult.state == "open")
    )

    if service:
        query = query.filter(ScanResult.service.ilike(f"%{service}%"))

    if port:
        query = query.filter(ScanResult.port == port)

    rows = (
        apply_asset_scope(query, current_user)
        .order_by(ScanResult.port)
        .limit(limit)
        .all()
    )

    return [
        {
            "port": row.port,
            "protocol": row.protocol,
            "service": row.service,
            "product": row.product,
            "version": row.version,
            "asset": row.asset_name,
        }
        for row in rows
    ]


def parse_and_search(
    db: Session,
    current_user: User,
    message: str,
) -> dict:
    """
    Parse a natural-language query and run the matching GuardianX queries.

    Returns the parsed predicates plus the structured result sets grouped by
    entity kind. Results are always scoped to the requesting user.
    """

    text = message.lower()

    severity = _parse_severity(text)
    service = _parse_service(text)
    port = _parse_port(text)
    asset_type = _parse_asset_type(text)
    cve = extract_cve(message)
    exposed = "exposed" in text or "internet" in text or "public" in text
    exploited = any(
        keyword in text
        for keyword in ("known exploited", "actively exploited", "cisa kev")
    )
    highest_epss = "epss" in text and (
        "highest" in text or "top" in text or "most likely" in text
    )

    parsed = {
        "severity": severity,
        "service": service,
        "port": port,
        "asset_type": asset_type,
        "cve": cve,
        "exposed": exposed,
        "exploited": exploited,
        "highest_epss": highest_epss,
    }

    findings = (
        _query_findings(
            db,
            current_user,
            severity=severity,
            service=service,
            port=port,
            cve=cve,
        )
        if (severity or service or port or cve)
        else []
    )

    assets = (
        _query_assets(
            db,
            current_user,
            asset_type=asset_type,
            service=service,
            port=port,
            exposed=exposed,
        )
        if (asset_type or service or port or exposed)
        else []
    )

    services = (
        _query_services(
            db,
            current_user,
            service=service,
            port=port,
        )
        if (service or port)
        else []
    )

    return {
        "parsed": parsed,
        "findings": findings,
        "assets": assets,
        "services": services,
    }
