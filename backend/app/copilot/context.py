"""
Builds structured, database-backed context for each Copilot intent.

All queries are ownership-scoped to the requesting user, so Copilot never
leaks data across users.
"""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.copilot import search as copilot_search
from app.copilot.intents import CopilotIntent, extract_cve
from app.integrations.threat_intel import epss as threat_intel_epss
from app.integrations.threat_intel import kev as threat_intel_kev
from app.integrations.threat_intel.service import get_cve_detail
from app.logger import logger
from app.models.asset import Asset
from app.models.finding import Finding
from app.models.scan import Scan
from app.models.scan_result import ScanResult
from app.models.user import User
from app.services import (
    asset_service,
    dashboard_service,
    finding_service,
    intelligence_service,
)
from app.services.query_helpers import apply_asset_scope
from app.services.scan_service import get_scans

_FINDING_COLUMNS = (
    Finding.id,
    Finding.title,
    Finding.description,
    Finding.severity,
    Finding.cve,
    Finding.cvss,
    Finding.status,
    Asset.name.label("asset_name"),
    ScanResult.service.label("service"),
)


def _query_findings(
    db: Session,
    current_user: User,
    cve: str | None = None,
    asset_id: int | None = None,
    limit: int = 10,
) -> list[dict]:
    """
    Query findings (scoped to the user) with joined asset/service info.
    """

    query = (
        db.query(*_FINDING_COLUMNS)
        .join(
            ScanResult,
            Finding.scan_result_id == ScanResult.id,
        )
        .join(
            Scan,
            ScanResult.scan_id == Scan.id,
        )
        .join(
            Asset,
            Scan.asset_id == Asset.id,
        )
    )

    if cve:
        query = query.filter(Finding.cve.ilike(f"%{cve}%"))

    if asset_id:
        query = query.filter(Scan.asset_id == asset_id)

    rows = (
        apply_asset_scope(query, current_user)
        .order_by(
            Finding.cvss.desc().nullslast(),
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "id": row.id,
            "title": row.title,
            "description": row.description,
            "severity": row.severity,
            "cve": row.cve,
            "cvss": row.cvss,
            "status": row.status,
            "asset": row.asset_name,
            "service": row.service,
        }
        for row in rows
    ]


def _resolve_asset(
    db: Session,
    current_user: User,
    message: str,
    asset_id: int | None,
):
    """
    Resolve an asset by id first, then by name appearing in the message.
    """

    if asset_id:
        asset = asset_service.get_asset_by_id(
            db,
            asset_id,
            current_user,
        )
        if asset:
            return asset

    if message:
        needle = message.lower()

        for asset in asset_service.get_all_assets(db, current_user):
            if asset.name.lower() in needle:
                return asset

    return None


def _resolve_finding(
    db: Session,
    current_user: User,
    finding_id: int | None,
    cve: str | None,
    asset: Asset | None,
) -> dict | None:
    """
    Resolve a finding by id, then by CVE, then by the highest-CVSS finding
    on the resolved asset.
    """

    if finding_id:
        detail = finding_service.get_finding(
            db,
            finding_id,
            current_user,
        )
        if detail:
            return detail

    rows = _query_findings(
        db,
        current_user,
        cve=cve,
        limit=1,
    )
    if rows:
        return rows[0]

    if asset is not None:
        rows = _query_findings(
            db,
            current_user,
            asset_id=asset.id,
            limit=1,
        )
        if rows:
            return rows[0]

    return None


def _build_resolved(
    cve: str | None,
    asset: Asset | None,
    finding: dict | None,
) -> dict:
    return {
        "cve": cve,
        "asset_id": asset.id if asset else None,
        "asset_name": asset.name if asset else None,
        "finding_id": finding.get("id") if finding else None,
        "finding_title": finding.get("title") if finding else None,
    }


# ---------------------------------------------------------------------
# Per-intent context builders
# ---------------------------------------------------------------------


def _ctx_explain_cve(db, current_user, cve) -> tuple[dict, dict, None]:
    findings = _query_findings(
        db,
        current_user,
        cve=cve,
        limit=10,
    )

    data = {
        "intent": CopilotIntent.EXPLAIN_CVE,
        "cve": cve,
        "findings": findings,
    }

    top = findings[0] if findings else None
    resolved = _build_resolved(cve, None, top)

    if top:
        resolved["asset_name"] = top.get("asset")

    return data, resolved, None


def _ctx_asset_risk(db, current_user, asset: Asset | None) -> tuple[dict | None, dict, str | None]:
    if asset is None:
        return None, _build_resolved(None, None, None), (
            "I couldn't find that asset in your scope. Include an asset id "
            "or the exact asset name in your request."
        )

    details = asset_service.get_asset_details(
        db,
        asset.id,
        current_user,
    )

    if details is None:
        return None, _build_resolved(None, asset, None), (
            "I couldn't load details for that asset. It may have been "
            "deleted or is not in your scope."
        )

    data = {
        "intent": CopilotIntent.ASSET_RISK,
        "asset": details,
        "open_ports": details.get("open_ports", []),
        "recent_findings": details.get("recent_findings", []),
    }

    return data, _build_resolved(None, asset, None), None


def _ctx_asset_summary(db, current_user) -> tuple[dict, dict, None]:
    assets = asset_service.get_all_assets(
        db,
        current_user,
    )

    by_type: dict[str, int] = {}
    by_environment: dict[str, int] = {}

    for asset in assets:
        asset_type = (
            asset.asset_type.value
            if hasattr(asset.asset_type, "value")
            else str(asset.asset_type)
        )
        environment = asset.environment or "unset"

        by_type[asset_type] = by_type.get(asset_type, 0) + 1
        by_environment[environment] = (
            by_environment.get(environment, 0) + 1
        )

    overview = dashboard_service.get_dashboard_overview(
        db,
        current_user,
    )

    data = {
        "intent": CopilotIntent.ASSET_SUMMARY,
        "total": len(assets),
        "by_type": by_type,
        "by_environment": by_environment,
        "overview": overview,
        "top_assets": overview.get("top_vulnerable_assets", []),
    }

    return data, _build_resolved(None, None, None), None


def _ctx_scan_summary(db, current_user) -> tuple[dict, dict, None]:
    today = datetime.now(UTC).date()

    scans = get_scans(db, current_user)

    today_scans = [
        scan
        for scan in scans
        if scan.started_at is not None
        and scan.started_at.date() == today
    ]

    by_status = {}
    for scan in today_scans:
        status = scan.status.value if hasattr(scan.status, "value") else scan.status
        by_status[status] = by_status.get(status, 0) + 1

    data = {
        "intent": CopilotIntent.SCAN_SUMMARY,
        "date": today.isoformat(),
        "total": len(today_scans),
        "by_status": by_status,
        "scans": [
            {
                "scan_id": scan.id,
                "asset_name": scan.asset_name,
                "status": (
                    scan.status.value
                    if hasattr(scan.status, "value")
                    else scan.status
                ),
                "started_at": scan.started_at,
                "finding_count": scan.finding_count,
            }
            for scan in today_scans
        ],
    }

    return data, _build_resolved(None, None, None), None


def _ctx_explain_vulnerability(
    db,
    current_user,
    finding: dict | None,
    cve: str | None,
    asset: Asset | None,
) -> tuple[dict | None, dict, str | None]:
    if finding is None:
        return None, _build_resolved(cve, asset, None), (
            "I couldn't resolve a specific vulnerability to explain. "
            "Reference a finding id, a CVE, or an asset name in your "
            "request."
        )

    data = {
        "intent": CopilotIntent.EXPLAIN_VULNERABILITY,
        "cve": cve or finding.get("cve"),
        "finding": finding,
    }

    return data, _build_resolved(cve, asset, finding), None


def _ctx_remediation(
    db,
    current_user,
    finding: dict | None,
    cve: str | None,
    asset: Asset | None,
) -> tuple[dict | None, dict, str | None]:
    if finding is None:
        return None, _build_resolved(cve, asset, None), (
            "I couldn't resolve a specific finding to remediate. Reference "
            "a finding id, a CVE, or an asset name in your request."
        )

    data = {
        "intent": CopilotIntent.REMEDIATION,
        "cve": cve or finding.get("cve"),
        "finding": finding,
    }

    return data, _build_resolved(cve, asset, finding), None


def _ctx_prioritize(db, current_user) -> tuple[dict, dict, None]:
    findings = finding_service.get_findings(
        db,
        current_user,
        severity=None,
        status=None,
        asset=None,
        scan=None,
        cve=None,
        search=None,
        page=1,
        size=10,
        sort_by="severity",
        sort_order="desc",
    )

    overview = dashboard_service.get_dashboard_overview(db, current_user)

    data = {
        "intent": CopilotIntent.PRIORITIZE,
        "overview": overview,
        "findings": findings.get("items", []),
        "top_assets": overview.get("top_vulnerable_assets", []),
    }

    return data, _build_resolved(None, None, None), None


def _ctx_executive_summary(db, current_user) -> tuple[dict, dict, None]:
    overview = dashboard_service.get_dashboard_overview(db, current_user)

    data = {
        "intent": CopilotIntent.EXECUTIVE_SUMMARY,
        "overview": overview,
        "top_assets": overview.get("top_vulnerable_assets", []),
    }

    return data, _build_resolved(None, None, None), None


def _ctx_security_recommendations(db, current_user) -> tuple[dict, dict, None]:
    findings = finding_service.get_findings(
        db,
        current_user,
        severity=None,
        status=None,
        asset=None,
        scan=None,
        cve=None,
        search=None,
        page=1,
        size=10,
        sort_by="severity",
        sort_order="desc",
    )

    overview = dashboard_service.get_dashboard_overview(db, current_user)

    data = {
        "intent": CopilotIntent.SECURITY_RECOMMENDATIONS,
        "overview": overview,
        "findings": findings.get("items", []),
        "top_assets": overview.get("top_vulnerable_assets", []),
        "open_ports": overview.get("open_ports", 0),
        "total_services": overview.get("total_services", 0),
    }

    return data, _build_resolved(None, None, None), None


def _ctx_general(db, current_user) -> tuple[dict, dict, None]:
    overview = dashboard_service.get_dashboard_overview(db, current_user)

    data = {
        "intent": CopilotIntent.GENERAL,
        "estate": {
            "assets": overview.get("assets", 0),
            "completed_scans": overview.get("completed_scans", 0),
            "total_findings": overview.get("total_findings", 0),
            "risk_score": overview.get("risk_score", 0),
        },
    }

    return data, _build_resolved(None, None, None), None


def _ctx_technical_summary(db, current_user) -> tuple[dict, dict, None]:
    overview = dashboard_service.get_dashboard_overview(db, current_user)

    findings = finding_service.get_findings(
        db,
        current_user,
        severity=None,
        status=None,
        asset=None,
        scan=None,
        cve=None,
        search=None,
        page=1,
        size=10,
        sort_by="severity",
        sort_order="desc",
    ).get("items", [])

    cve_ids = [
        finding["cve"]
        for finding in findings
        if finding.get("cve")
    ]

    epss_scores: dict[str, dict] = {}
    kev_status: dict[str, bool] = {}

    try:
        if cve_ids:
            epss_scores = threat_intel_epss.get_epss_scores(cve_ids)
    except Exception:
        logger.warning(
            "[Copilot] EPSS enrichment failed for technical summary",
            exc_info=True,
        )

    try:
        kev_status = {
            cve_id: threat_intel_kev.is_exploited(cve_id)
            for cve_id in cve_ids
        }
    except Exception:
        logger.warning(
            "[Copilot] KEV enrichment failed for technical summary",
            exc_info=True,
        )

    for finding in findings:
        cve_id = finding.get("cve")
        finding["epss_score"] = (
            epss_scores.get(cve_id, {}).get("score")
            if cve_id
            else None
        )
        finding["exploited"] = (
            kev_status.get(cve_id, False)
            if cve_id
            else False
        )

    data = {
        "intent": CopilotIntent.TECHNICAL_SUMMARY,
        "overview": overview,
        "findings": findings,
        "open_ports": overview.get("open_ports", 0),
        "total_services": overview.get("total_services", 0),
        "top_vulnerabilities": overview.get("top_vulnerabilities", []),
    }

    return data, _build_resolved(None, None, None), None


def _ctx_dashboard_insights(db, current_user) -> tuple[dict, dict, None]:
    overview = dashboard_service.get_dashboard_overview(db, current_user)

    data = {
        "intent": CopilotIntent.DASHBOARD_INSIGHTS,
        "overview": overview,
        "risk_trend": overview.get("risk_trend", []),
        "findings_trend": overview.get("findings_trend", []),
        "asset_distribution": overview.get("asset_distribution", []),
        "top_vulnerable_assets": overview.get("top_vulnerable_assets", []),
        "top_vulnerabilities": overview.get("top_vulnerabilities", []),
        "open_ports": overview.get("open_ports", 0),
        "total_services": overview.get("total_services", 0),
    }

    return data, _build_resolved(None, None, None), None


def _ctx_natural_language_search(
    db,
    current_user,
    message: str,
) -> tuple[dict, dict, None]:
    results = copilot_search.parse_and_search(
        db,
        current_user,
        message,
    )

    data = {
        "intent": CopilotIntent.NATURAL_LANGUAGE_SEARCH,
        "query": message,
        "parsed": results["parsed"],
        "findings": results["findings"],
        "assets": results["assets"],
        "services": results["services"],
    }

    return data, _build_resolved(None, None, None), None


def _ctx_threat_summary(
    db,
    current_user,
    cve: str | None,
    finding: dict | None,
    asset: Asset | None,
) -> tuple[dict | None, dict, str | None]:
    cve_id = cve or (finding.get("cve") if finding else None)

    if cve_id is None:
        return (
            None,
            _build_resolved(None, asset, finding),
            (
                "I couldn't resolve a CVE to build a threat summary for. "
                "Reference a CVE identifier or a finding id in your request."
            ),
        )

    enriched: dict = {}

    try:
        enriched = get_cve_detail(cve_id)
    except Exception:
        logger.warning(
            "[Copilot] Threat intel enrichment failed for %s",
            cve_id,
            exc_info=True,
        )

    vt_report: dict | None = None
    lookup_target = None

    if asset and asset.ip_address:
        lookup_target = asset.ip_address
    elif asset and asset.domain:
        lookup_target = asset.domain

    if lookup_target:
        try:
            result = intelligence_service.lookup(
                db,
                current_user.id,
                lookup_target,
            )
            report = result.report
            vt_report = {
                "resource": report.resource,
                "risk_score": report.risk_score,
                "threat_level": (
                    report.threat_level.value
                    if hasattr(report.threat_level, "value")
                    else str(report.threat_level)
                ),
                "detection_ratio": report.detection_ratio,
                "detected": report.detected,
            }
        except Exception:
            logger.warning(
                "[Copilot] VirusTotal enrichment unavailable for %s",
                lookup_target,
                exc_info=True,
            )

    data = {
        "intent": CopilotIntent.THREAT_SUMMARY,
        "cve": cve_id,
        "finding": finding,
        "nvd": {
            "title": enriched.get("title"),
            "description": enriched.get("description"),
            "severity": enriched.get("severity"),
            "cvss_score": enriched.get("cvss_score"),
        }
        if enriched
        else None,
        "epss_score": enriched.get("epss_score"),
        "epss_percentile": enriched.get("epss_percentile"),
        "exploited": enriched.get("exploited", False),
        "kev_due_date": enriched.get("kev_due_date"),
        "attack_techniques": enriched.get("attack_techniques", []),
        "advisories": enriched.get("advisories", []),
        "guardianx_risk_score": enriched.get("guardianx_risk_score"),
        "threat_level": enriched.get("threat_level"),
        "virustotal": vt_report,
    }

    return data, _build_resolved(cve_id, asset, finding), None


# ---------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------

_BUILDERS = {
    CopilotIntent.EXPLAIN_CVE: _ctx_explain_cve,
    CopilotIntent.EXPLAIN_VULNERABILITY: _ctx_explain_vulnerability,
    CopilotIntent.ASSET_RISK: _ctx_asset_risk,
    CopilotIntent.SCAN_SUMMARY: _ctx_scan_summary,
    CopilotIntent.ASSET_SUMMARY: _ctx_asset_summary,
    CopilotIntent.REMEDIATION: _ctx_remediation,
    CopilotIntent.PRIORITIZE: _ctx_prioritize,
    CopilotIntent.EXECUTIVE_SUMMARY: _ctx_executive_summary,
    CopilotIntent.TECHNICAL_SUMMARY: _ctx_technical_summary,
    CopilotIntent.DASHBOARD_INSIGHTS: _ctx_dashboard_insights,
    CopilotIntent.THREAT_SUMMARY: _ctx_threat_summary,
    CopilotIntent.NATURAL_LANGUAGE_SEARCH: _ctx_natural_language_search,
    CopilotIntent.SECURITY_RECOMMENDATIONS: _ctx_security_recommendations,
    CopilotIntent.GENERAL: _ctx_general,
}


def build_context(db: Session, current_user: User, request, intent: CopilotIntent) -> dict:
    """
    Build the structured context payload for an intent.

    Returns `{"data": dict|None, "resolved": dict, "reason": str|None}`.
    `data` is None (with a `reason`) when the intent's target resource
    could not be resolved.
    """

    message = request.message or ""
    cve = (request.cve or "").strip() or extract_cve(message)
    asset = _resolve_asset(
        db,
        current_user,
        message,
        request.asset_id,
    )

    builder = _BUILDERS[intent]

    if intent == CopilotIntent.EXPLAIN_CVE:
        if cve is None:
            return {
                "data": None,
                "resolved": _build_resolved(None, None, None),
                "reason": (
                    "Which CVE would you like me to explain? Provide an "
                    "identifier such as CVE-2024-1234."
                ),
            }
        data, resolved, reason = builder(db, current_user, cve)

    elif intent == CopilotIntent.REMEDIATION:
        finding = _resolve_finding(
            db,
            current_user,
            request.finding_id,
            cve,
            asset,
        )
        if cve is None and finding:
            cve = finding.get("cve")
        data, resolved, reason = builder(
            db,
            current_user,
            finding,
            cve,
            asset,
        )

    elif intent == CopilotIntent.EXPLAIN_VULNERABILITY:
        finding = _resolve_finding(
            db,
            current_user,
            request.finding_id,
            cve,
            asset,
        )
        if cve is None and finding:
            cve = finding.get("cve")
        data, resolved, reason = builder(
            db,
            current_user,
            finding,
            cve,
            asset,
        )

    elif intent == CopilotIntent.THREAT_SUMMARY:
        finding = _resolve_finding(
            db,
            current_user,
            request.finding_id,
            cve,
            asset,
        )
        if cve is None and finding:
            cve = finding.get("cve")
        data, resolved, reason = builder(
            db,
            current_user,
            cve,
            finding,
            asset,
        )

    elif intent == CopilotIntent.NATURAL_LANGUAGE_SEARCH:
        data, resolved, reason = builder(db, current_user, message)

    elif intent == CopilotIntent.ASSET_RISK:
        data, resolved, reason = builder(db, current_user, asset)

    else:
        data, resolved, reason = builder(db, current_user)

    return {
        "data": data,
        "resolved": resolved,
        "reason": reason,
    }
