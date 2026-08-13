"""Threat Intelligence orchestration layer.

Combines NVD, CISA KEV, FIRST EPSS and MITRE ATT&CK into dashboard-ready
responses. Enrichment is bounded: EPSS lookups are batched, KEV is a single
cached catalog, and every source degrades gracefully so the dashboard still
renders when a feed is unreachable.
"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, date, datetime, timedelta

from app.core.exceptions import ResourceNotFoundError
from app.integrations.threat_intel import attack, epss, epss_history, kev, nvd

_WINDOW_PAGES = 2
_EPSS_BUCKETS = (
    ("Very Low (<1%)", lambda score: score < 0.01),
    ("Low (1-10%)", lambda score: 0.01 <= score < 0.10),
    ("Medium (10-30%)", lambda score: 0.10 <= score < 0.30),
    ("High (30-70%)", lambda score: 0.30 <= score < 0.70),
    ("Very High (>70%)", lambda score: score >= 0.70),
)


def _guardianx_risk(cve: dict) -> tuple[int, str, str, str]:
    """Create an explainable 0-100 prioritization score from external intel."""
    cvss = float(cve.get("cvss_score") or 0)
    epss_score = float(cve.get("epss_score") or 0)
    actively_exploited = bool(cve.get("exploited"))
    # CVSS provides impact; EPSS predicts near-term exploitation. KEV is a
    # deterministic operational signal and receives a material escalation.
    score = min(100, round((cvss * 6) + (epss_score * 35) + (30 if actively_exploited else 0)))
    level = "CRITICAL" if score >= 85 else "HIGH" if score >= 65 else "MEDIUM" if score >= 35 else "LOW"
    exploit_status = "Actively Exploited (CISA KEV)" if actively_exploited else (
        "High exploit probability" if epss_score >= 0.30 else "No known active exploitation"
    )
    summary = (
        f"{cve['id']} is rated {cve.get('severity', 'UNKNOWN')} (CVSS {cvss:.1f}). "
        f"EPSS estimates a {epss_score * 100:.1f}% exploitation probability. "
        + ("CISA lists this vulnerability as actively exploited; prioritize remediation immediately." if actively_exploited else "Prioritize according to affected asset exposure and patch availability.")
    )
    return score, level, exploit_status, summary


def _enrich(
    cves: list[dict],
    *,
    with_attack: bool = False,
) -> list[dict]:
    """Attach EPSS + KEV context to a list of normalized CVEs."""

    ids = [cve["id"] for cve in cves]
    epss_scores = epss.get_epss_scores(ids)
    kev_entries = {
        entry["cve_id"]: entry
        for entry in kev.get_kev_catalog()
    }

    for cve in cves:
        cve_id = cve["id"]

        score = epss_scores.get(cve_id)
        cve["epss_score"] = score.get("score") if score else None
        cve["epss_percentile"] = score.get("percentile") if score else None

        kev_entry = kev_entries.get(cve_id)
        cve["exploited"] = kev_entry is not None
        cve["kev_due_date"] = kev_entry.get("due_date") if kev_entry else None
        risk_score, threat_level, exploit_status, ai_summary = _guardianx_risk(cve)
        cve["guardianx_risk_score"] = risk_score
        cve["threat_level"] = threat_level
        cve["exploit_status"] = exploit_status
        cve["ai_summary"] = ai_summary

        if with_attack:
            cve["attack_techniques"] = attack.map_cwes_to_techniques(
                cve.get("cwes") or []
            )

    return cves


def get_trending(
    days: int = 14,
    limit: int = 10,
) -> dict:
    """Most recently published CVEs in the last `days`, enriched."""

    days = max(1, min(days, 90))
    limit = max(1, min(limit, 50))

    cves = nvd.search_cves(days=days, limit=limit)
    cves.sort(key=lambda cve: cve.get("published") or "", reverse=True)
    cves = cves[:limit]

    return {
        "window_days": days,
        "total": len(cves),
        "items": _enrich(cves),
    }


def search_cves(
    query: str | None = None,
    severity: str | None = None,
    year: int | None = None,
    vendor: str | None = None,
    exploited_only: bool = False,
    sort_by: str = "published",
    limit: int = 20,
) -> dict:
    """Search NVD with optional severity/year/KEV filters, enriched."""

    limit = max(1, min(limit, 50))

    cves = nvd.search_cves(
        query=query or None,
        severity=severity or None,
        year=year,
        limit=limit,
    )
    if vendor:
        needle = vendor.strip().lower()
        cves = [
            cve for cve in cves
            if needle in " ".join(cve.get("affected_vendors") or [cve.get("vendor") or ""]).lower()
        ]

    enriched = _enrich(cves)

    if exploited_only:
        enriched = [cve for cve in enriched if cve["exploited"]]

    if sort_by == "epss":
        enriched.sort(key=lambda cve: cve.get("epss_score") or 0, reverse=True)
    elif sort_by == "risk":
        enriched.sort(key=lambda cve: cve.get("guardianx_risk_score") or 0, reverse=True)
    else:
        enriched.sort(key=lambda cve: cve.get("published") or "", reverse=True)

    enriched = enriched[:limit]

    return {
        "query": query or "",
        "severity": severity or None,
        "year": year,
        "vendor": vendor or None,
        "exploited_only": exploited_only,
        "sort": sort_by,
        "total": len(enriched),
        "items": enriched,
    }


def _extract_advisories(references: list[dict]) -> list[dict]:
    """References carrying an advisory/patch/exploit tag."""

    advisory_tags = {
        "vendor advisory",
        "patch",
        "mitigation",
        "exploit",
        "third party advisory",
    }

    advisories: list[dict] = []
    for reference in references:
        tags = {
            tag.lower()
            for tag in reference.get("tags") or []
        }
        if tags and (tags & advisory_tags):
            advisories.append(reference)

    return advisories


def get_cve_detail(cve_id: str) -> dict:
    """Full CVE enrichment: EPSS, KEV status, ATT&CK and vendor advisories."""

    cve = nvd.get_cve(cve_id)

    if cve is None:
        raise ResourceNotFoundError(
            f"No vulnerability intelligence found for {cve_id.upper()}."
        )

    enriched = _enrich([cve], with_attack=True)[0]
    enriched["advisories"] = _extract_advisories(enriched.get("references") or [])

    if enriched.get("epss_score") is not None:
        epss_history.record_snapshot(
            enriched["id"],
            float(enriched["epss_score"]),
            float(enriched.get("epss_percentile") or 0),
        )
        enriched["epss_history"] = epss_history.get_history(enriched["id"])
    else:
        enriched["epss_history"] = []

    return enriched


def _window_cves(days: int) -> list[dict]:
    """Fetch a bounded window of recent CVEs for aggregate stats."""

    cves: list[dict] = []
    limit = min(days * 60, 200)

    for page in range(_WINDOW_PAGES):
        page_cves = nvd.search_cves(days=days, limit=limit)
        if not page_cves:
            break
        cves.extend(page_cves)
        if len(page_cves) < limit:
            break

    return cves


def _build_timeline(
    cves: list[dict],
    days: int,
) -> list[dict]:
    today = datetime.now(UTC).date()
    start = today - timedelta(days=days - 1)

    by_day: dict[date, list[dict]] = {d: [] for d in _date_range(start, today)}

    for cve in cves:
        published = cve.get("published")
        if not published:
            continue
        try:
            day = datetime.fromisoformat(published).date()
        except ValueError:
            continue
        if day in by_day:
            by_day[day].append(cve)

    timeline: list[dict] = []
    for day in sorted(by_day):
        day_cves = by_day[day]
        scores = [
            cve["epss_score"]
            for cve in day_cves
            if cve.get("epss_score") is not None
        ]
        avg = round(sum(scores) / len(scores), 3) if scores else 0.0
        timeline.append(
            {
                "date": day.isoformat(),
                "published_count": len(day_cves),
                "avg_epss": avg,
            }
        )

    return timeline


def _date_range(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def get_stats(days: int = 14) -> dict:
    """Aggregate severity/EPSS distributions and a risk timeline."""

    days = max(1, min(days, 60))

    cves = _window_cves(days)
    cves = _enrich(cves)

    severity_counter: Counter[str] = Counter()
    for cve in cves:
        severity_counter[cve.get("severity") or "UNKNOWN"] += 1

    epss_counter: Counter[str] = Counter()
    for cve in cves:
        score = cve.get("epss_score")
        if score is None:
            continue
        for label, predicate in _EPSS_BUCKETS:
            if predicate(score):
                epss_counter[label] += 1
                break

    severity_order = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN")
    severity_distribution = [
        {"severity": level, "count": severity_counter.get(level, 0)}
        for level in severity_order
    ]

    epss_distribution = [
        {"bucket": label, "count": epss_counter.get(label, 0)}
        for label, _ in _EPSS_BUCKETS
    ]

    scores = [
        cve["epss_score"] for cve in cves if cve.get("epss_score") is not None
    ]
    avg_epss = round(sum(scores) / len(scores), 4) if scores else 0.0

    sources = [
        {
            "source": "nvd",
            "configured": True,
            "healthy": nvd.is_healthy(),
        },
        {
            "source": "cisa_kev",
            "configured": True,
            "healthy": kev.is_healthy(),
        },
        {
            "source": "epss",
            "configured": True,
            "healthy": epss.is_healthy(),
        },
        {
            "source": "mitre_attck",
            "configured": True,
            "healthy": True,
        },
    ]

    return {
        "total_cves": len(cves),
        "critical": severity_counter.get("CRITICAL", 0),
        "high": severity_counter.get("HIGH", 0),
        "medium": severity_counter.get("MEDIUM", 0),
        "low": severity_counter.get("LOW", 0),
        "exploited_count": sum(1 for cve in cves if cve["exploited"]),
        "avg_epss": avg_epss,
        "severity_distribution": severity_distribution,
        "epss_distribution": epss_distribution,
        "risk_timeline": _build_timeline(cves, days),
        "sources": sources,
    }


def get_kev_catalog(limit: int = 25) -> list[dict]:
    """Return the KEV catalog sorted by most recently added, bounded."""

    limit = max(1, min(limit, 100))

    entries = kev.get_kev_catalog()
    entries.sort(
        key=lambda entry: entry.get("date_added") or "",
        reverse=True,
    )

    return entries[:limit]


def get_attack_techniques(tactic: str | None = None) -> list[dict]:
    return attack.get_techniques(tactic)
