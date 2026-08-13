from __future__ import annotations

from collections import Counter
from datetime import datetime, UTC
from typing import Iterable

from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.exceptions import ResourceNotFoundError
from app.models.asset import Asset
from app.models.finding import Finding
from app.models.scan import Scan
from app.models.scan_result import ScanResult
from app.models.user import User

from app.schemas.report import (
    AssetReport,
    ExecutiveReport,
    ExecutiveSummary,
    FindingReport,
    ScanSummary,
    ServiceReport,
    TechnicalReport,
)

from app.services.query_helpers import apply_asset_scope
from app.services.risk_service import calculate_risk_score


# ---------------------------------------------------------------------
# Query Helpers
# ---------------------------------------------------------------------


def _get_scan(
    db: Session,
    scan_id: int,
    current_user: User,
) -> Scan:
    query = (
        db.query(Scan)
        .join(Asset)
        .options(
            joinedload(Scan.asset),
            selectinload(Scan.results).selectinload(ScanResult.findings),
        )
    )

    query = apply_asset_scope(query, current_user)

    scan = query.filter(Scan.id == scan_id).first()

    if scan is None:
        raise ResourceNotFoundError("Scan not found.")

    return scan


def _get_asset(
    db: Session,
    asset_id: int,
    current_user: User,
) -> Asset:
    query = (
        db.query(Asset)
        .options(
            selectinload(Asset.scans)
            .selectinload(Scan.results)
            .selectinload(ScanResult.findings)
        )
    )

    query = apply_asset_scope(query, current_user)

    asset = query.filter(Asset.id == asset_id).first()

    if asset is None:
        raise ResourceNotFoundError("Asset not found.")

    return asset


# ---------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------


def _build_service_reports(
    results: Iterable[ScanResult],
) -> list[ServiceReport]:
    services: list[ServiceReport] = []

    for result in results:
        services.append(
            ServiceReport(
                port=result.port,
                protocol=result.protocol,
                service=result.service,
                product=result.product,
                version=result.version,
                state=result.state,
                cpe=result.cpe,
            )
        )

    return services


def _build_finding_reports(
    findings: Iterable[Finding],
) -> list[FindingReport]:
    reports: list[FindingReport] = []

    for finding in findings:
        reports.append(
            FindingReport(
                cve=finding.cve,
                title=finding.title,
                severity=finding.severity,
                cvss=finding.cvss,
                status=finding.status,
                description=finding.description,
                recommendation=finding.recommendation,
                affected_service=(
                    finding.scan_result.service
                    if finding.scan_result
                    else None
                ),
            )
        )

    return reports


# ---------------------------------------------------------------------
# Summary Helpers
# ---------------------------------------------------------------------


def _severity_counts(findings: Iterable[Finding]) -> Counter:
    counter: Counter = Counter()

    for finding in findings:
        counter[finding.severity.lower()] += 1

    return counter


def _asset_risk_score(findings):
    critical = 0
    high = 0
    medium = 0
    low = 0

    for finding in findings:
        severity = (finding.severity or "").upper()

        if severity == "CRITICAL":
            critical += 1
        elif severity == "HIGH":
            high += 1
        elif severity == "MEDIUM":
            medium += 1
        elif severity == "LOW":
            low += 1

    return calculate_risk_score(
        critical=critical,
        high=high,
        medium=medium,
        low=low,
    )

def _build_asset_report(asset: Asset) -> AssetReport:
    all_results: list[ScanResult] = []
    all_findings: list[Finding] = []

    for scan in asset.scans:
        all_results.extend(scan.results)

        for result in scan.results:
            all_findings.extend(result.findings)

    counts = _severity_counts(all_findings)

    latest_scan = None

    if asset.scans:
        latest_scan = max(
            asset.scans,
            key=lambda s: s.created_at,
        )

    return AssetReport(
        id=asset.id,
        name=asset.name,
        domain=asset.domain,
        ip_address=asset.ip_address,
        asset_type=str(asset.asset_type),
        risk_score=_asset_risk_score(all_findings),
        critical=counts["critical"],
        high=counts["high"],
        medium=counts["medium"],
        low=counts["low"],
        total_findings=len(all_findings),
        services=_build_service_reports(all_results),
        findings=_build_finding_reports(all_findings),
        last_scan=latest_scan.finished_at if latest_scan else None,
        scanner=latest_scan.scanner if latest_scan else None,
    )


def _build_scan_summary(scan: Scan) -> ScanSummary:
    return ScanSummary(
        id=scan.id,
        status=str(scan.status),
        started_at=scan.started_at,
        finished_at=scan.finished_at,
    )


def _build_executive_summary(
    assets: list[AssetReport],
    scan_count: int,
) -> ExecutiveSummary:
    critical = sum(a.critical for a in assets)
    high = sum(a.high for a in assets)
    medium = sum(a.medium for a in assets)
    low = sum(a.low for a in assets)

    total = critical + high + medium + low

    risk = 0

    if assets:
        risk = round(
            sum(a.risk_score for a in assets)
            / len(assets)
        )

    return ExecutiveSummary(
        assets=len(assets),
        scans=scan_count,
        critical=critical,
        high=high,
        medium=medium,
        low=low,
        total_findings=total,
        risk_score=risk,
    )
# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------




def build_scan_report(
    db: Session,
    scan_id: int,
    current_user: User,
) -> TechnicalReport:
    scan = _get_scan(
        db=db,
        scan_id=scan_id,
        current_user=current_user,
    )

    findings: list[Finding] = []

    for result in scan.results:
        findings.extend(result.findings)

    asset_report = _build_asset_report(scan.asset)

    return TechnicalReport(
        generated_at=datetime.now(UTC),
        scan=_build_scan_summary(scan),
        asset=asset_report,
        findings=_build_finding_reports(findings),
    )


def build_asset_report(
    db: Session,
    asset_id: int,
    current_user: User,
) -> AssetReport:
    asset = _get_asset(
        db=db,
        asset_id=asset_id,
        current_user=current_user,
    )

    return _build_asset_report(asset)


def build_executive_report(
    db: Session,
    current_user: User,
) -> ExecutiveReport:
    query = db.query(Asset)

    query = apply_asset_scope(query, current_user)

    assets = query.options(
        selectinload(Asset.scans)
        .selectinload(Scan.results)
        .selectinload(ScanResult.findings)
    ).all()

    scan_count = sum(len(asset.scans) for asset in assets)
    asset_reports = [
        _build_asset_report(asset)
        for asset in assets
    ]

    summary = _build_executive_summary(
    asset_reports,
    scan_count,
)


    recommendations: list[str] = []

    if summary.critical:
        recommendations.append(
            "Immediately remediate all Critical vulnerabilities."
        )

    if summary.high:
        recommendations.append(
            "Prioritize remediation of High severity findings."
        )

    if summary.medium:
        recommendations.append(
            "Schedule Medium severity findings into the next maintenance window."
        )

    if summary.low:
        recommendations.append(
            "Review Low severity findings during routine hardening."
        )

    if not recommendations:
        recommendations.append(
            "No significant vulnerabilities detected."
        )

    asset_reports.sort(
        key=lambda asset: asset.risk_score,
        reverse=True,
    )

    return ExecutiveReport(
        generated_at=datetime.now(UTC),
        summary=summary,
        top_assets=asset_reports[:5],
        recommendations=recommendations,
    )
