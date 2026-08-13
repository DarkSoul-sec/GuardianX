from __future__ import annotations

import ipaddress
from typing import Any

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.finding import Finding
from app.models.scan import Scan
from app.models.scan_result import ScanResult
from app.models.user import User
from app.schemas.asset import AssetCreate, AssetUpdate
from app.services.query_helpers import apply_asset_scope
from app.services.risk_service import calculate_risk_score
from app.copilot.summary import generate_asset_summary


def get_asset_by_id(
    db: Session,
    asset_id: int,
    current_user: User,
) -> Asset | None:
    query = db.query(Asset).filter(Asset.id == asset_id)

    query = apply_asset_scope(
    query,
    current_user,
)

    return query.first()


def get_all_assets(
    db: Session,
    current_user: User,
) -> list[Asset]:
    query = db.query(Asset)

    query = apply_asset_scope(
        query,
        current_user,
    )

    return query.order_by(Asset.id).all()


def create_asset(
    db: Session,
    asset: AssetCreate,
    created_by: int,
) -> Asset:
    db_asset = Asset(
        **asset.model_dump(),
        created_by=created_by,
    )

    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)

    return db_asset


def update_asset(
    db: Session,
    asset: Asset,
    data: AssetUpdate,
) -> Asset:
    update_data = data.model_dump(
        exclude_unset=True,
    )

    for key, value in update_data.items():
        setattr(
            asset,
            key,
            value,
        )

    db.commit()
    db.refresh(asset)

    return asset


def _get_severity_summary(
    db: Session,
    asset_id: int,
):
    return (
        db.query(
            func.sum(
                case(
                    (Finding.severity == "CRITICAL", 1),
                    else_=0,
                )
            ).label("critical"),
            func.sum(
                case(
                    (Finding.severity == "HIGH", 1),
                    else_=0,
                )
            ).label("high"),
            func.sum(
                case(
                    (Finding.severity == "MEDIUM", 1),
                    else_=0,
                )
            ).label("medium"),
            func.sum(
                case(
                    (Finding.severity == "LOW", 1),
                    else_=0,
                )
            ).label("low"),
            func.count(Finding.id).label("total_findings"),
        )
        .join(
            ScanResult,
            Finding.scan_result_id == ScanResult.id,
        )
        .join(
            Scan,
            ScanResult.scan_id == Scan.id,
        )
        .filter(
            Scan.asset_id == asset_id,
        )
        .first()
    )
def _get_services(
    db: Session,
    asset_id: int,
):
    return (
        db.query(
            ScanResult.port,
            ScanResult.protocol,
            ScanResult.product,
            ScanResult.version,
            ScanResult.cpe,
            ScanResult.state,
        )
        .join(
            Scan,
            ScanResult.scan_id == Scan.id,
        )
        .filter(
            Scan.asset_id == asset_id,
        )
        .order_by(
            ScanResult.port.asc(),
        )
        .all()
    )
def _get_open_ports(
    services,
) -> list[int]:
    """
    Return all unique open ports.
    """

    return sorted(
        {
            service.port
            for service in services
            if service.state == "open"
        }
    )


def _get_technologies(
    services,
) -> list[str]:
    """
    Return detected technologies.
    """

    technologies = set()

    for service in services:

        if service.product:
            technologies.add(service.product)

    return sorted(technologies)


def _classify_internet_facing(ip: str | None) -> bool:
    """
    Return True when the asset lives on a public (globally routable) IP.

    Loopback, private, link-local, reserved, multicast and documentation
    ranges are treated as non-internet-facing.
    """

    if not ip:
        return False

    try:
        address = ipaddress.ip_address(ip.strip())
    except ValueError:
        return False

    return bool(
        not address.is_private
        and not address.is_loopback
        and not address.is_link_local
        and not address.is_multicast
        and not address.is_reserved
        and not address.is_unspecified
    )


def _compute_attack_surface(
    open_ports: list[int],
    total_findings: int,
    internet_facing: bool,
) -> int:
    """
    Score the exposed attack surface on a 0-100 scale.

    Exposed ports drive the base score, findings add weight, and
    internet-facing assets get an exposure bonus.
    """

    port_score = min(50, len(open_ports) * 5)
    finding_score = min(30, total_findings * 2)
    exposure = 20 if internet_facing else 0

    return min(100, port_score + finding_score + exposure)
def _get_recent_scans(
    db: Session,
    asset_id: int,
):
    scan_finding_counts = (
        db.query(
            ScanResult.scan_id.label("scan_id"),
            func.count(Finding.id).label("total_findings"),
        )
        .join(
            Finding,
            Finding.scan_result_id == ScanResult.id,
            isouter=True,
        )
        .group_by(
            ScanResult.scan_id,
        )
        .subquery()
    )

    return (
        db.query(
            Scan.id.label("scan_id"),
            Scan.status,
            Scan.started_at,
            Scan.finished_at,
            func.coalesce(
                scan_finding_counts.c.total_findings,
                0,
            ).label("total_findings"),
        )
        .outerjoin(
            scan_finding_counts,
            scan_finding_counts.c.scan_id == Scan.id,
        )
        .filter(
            Scan.asset_id == asset_id,
        )
        .order_by(
            Scan.started_at.desc().nullslast(),
            Scan.id.desc(),
        )
        .limit(5)
        .all()
    )
def _get_recent_findings(
    db: Session,
    asset_id: int,
):
    return (
        db.query(
            Finding.cve,
            Finding.severity,
            Finding.title,
            Finding.status,
            Finding.recommendation,
            Finding.cvss,
        )
        .join(
            ScanResult,
            Finding.scan_result_id == ScanResult.id,
        )
        .join(
            Scan,
            ScanResult.scan_id == Scan.id,
        )
        .filter(
            Scan.asset_id == asset_id,
        )
        .order_by(
            Finding.created_at.desc(),
        )
        .limit(10)
        .all()
    )
def get_asset_details(
    db: Session,
    asset_id: int,
    current_user: User,
) -> dict[str, Any] | None:
    """
    Return the complete asset details payload.

    The heavy database work is delegated to helper functions to keep this
    function concise and maintainable.
    """

    asset = get_asset_by_id(
        db,
        asset_id,
        current_user,
    )

    if asset is None:
        return None

    severity = _get_severity_summary(
        db,
        asset_id,
    )

    services = _get_services(
        db,
        asset_id,
    )

    recent_scans = _get_recent_scans(
        db,
        asset_id,
    )

    recent_findings = _get_recent_findings(
        db,
        asset_id,
    )

    critical = severity.critical or 0
    high = severity.high or 0
    medium = severity.medium or 0
    low = severity.low or 0
    total_findings = severity.total_findings or 0
    security_score = max(
        0,
        100 - calculate_risk_score(
            critical=critical,
            high=high,
            medium=medium,
            low=low,
        ),
    )

    open_ports = _get_open_ports(
        services,
    )

    technologies = _get_technologies(
        services,
    )

    internet_facing = _classify_internet_facing(
        asset.ip_address,
    )

    attack_surface_score = _compute_attack_surface(
        open_ports=open_ports,
        total_findings=total_findings,
        internet_facing=internet_facing,
    )

    ai_summary = generate_asset_summary(
        asset.id,
        {
            "name": asset.name,
            "asset_type": asset.asset_type,
            "ip_address": asset.ip_address,
            "environment": asset.environment,
            "criticality": asset.criticality,
            "internet_facing": internet_facing,
            "risk_score": calculate_risk_score(
                critical=critical,
                high=high,
                medium=medium,
                low=low,
            ),
            "attack_surface_score": attack_surface_score,
            "total_findings": total_findings,
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low,
            "open_ports": open_ports,
            "technologies": technologies,
        },
    )

    return {
        "id": asset.id,
        "name": asset.name,
        "hostname": asset.domain,
        "ip_address": asset.ip_address,
        "asset_type": asset.asset_type,
        "created_at": asset.created_at,
        "updated_at": asset.updated_at,
        "risk_score": calculate_risk_score(
            critical=critical,
            high=high,
            medium=medium,
            low=low,
        ),
        "total_findings": total_findings,
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low,
        "services": [
            {
                "port": row.port,
                "protocol": row.protocol,
                "product": row.product,
                "version": row.version,
                "cpe": row.cpe,
                "state": row.state,
            }
            for row in services
        ],
        "recent_scans": [
            {
                "scan_id": row.scan_id,
                "status": (
                    row.status.value
                    if hasattr(row.status, "value")
                    else row.status
                ),
                "started_at": row.started_at,
                "finished_at": row.finished_at,
                "total_findings": row.total_findings,
            }
            for row in recent_scans
        ],
        "domain": asset.domain,

        "operating_system": asset.operating_system,

        "environment": asset.environment,

        "owner": asset.owner,

        "criticality": asset.criticality,

        "description": asset.description,

        "security_score": security_score,

        "open_ports": open_ports,

        "technologies": technologies,

        "internet_facing": internet_facing,

        "attack_surface_score": attack_surface_score,

        "ai_summary": ai_summary,
        "recent_findings": [
            {
                "cve": row.cve,
                "severity": row.severity,
                "title": row.title,
                "status": row.status,
                "recommendation": row.recommendation,
            }
            for row in recent_findings
        ],
    }
def delete_asset(
    db: Session,
    asset: Asset,
) -> None:
    db.delete(asset)
    db.commit()
