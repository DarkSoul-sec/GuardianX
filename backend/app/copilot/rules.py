"""
Deterministic, database-backed provider used when no LLM is configured.

This is a first-class provider: it implements BaseCopilotProvider and can
be swapped for OpenAI, Gemini or Ollama without changing any other code.
"""

from datetime import UTC, datetime

from app.copilot.base import BaseCopilotProvider
from app.copilot.intents import CopilotIntent


def _fmt_cvss(value) -> str:
    return f"{value:.1f}" if value is not None else "N/A"


def _fmt_datetime(value) -> str:
    if not value:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M")


def _render_explain_cve(ctx: dict) -> str:
    cve = ctx.get("cve") or "the referenced CVE"
    findings = ctx.get("findings", [])

    if not findings:
        return (
            f"### {cve}\n\n"
            "This CVE is **not currently detected** in your monitored "
            "assets, so GuardianX has no exposure data for it.\n\n"
            f"- **CVE:** {cve}\n"
            "- **Affected assets:** none detected\n\n"
            "Run a scan against the relevant assets or consult the vendor "
            "advisory for details."
        )

    top = findings[0]
    description = (top.get("description") or "").strip()

    lines = [
        f"### {cve} — {top.get('title') or 'Vulnerability'}",
        "",
        f"- **Severity:** {top.get('severity', 'UNKNOWN')} · "
        f"**CVSS:** {_fmt_cvss(top.get('cvss'))} · "
        f"**Status:** {top.get('status', 'OPEN')}",
    ]

    if description:
        lines += ["", description]

    affected = ", ".join(
        dict.fromkeys(
            finding.get("asset")
            for finding in findings
            if finding.get("asset")
        )
    )
    lines += [
        "",
        f"**Affected assets:** {affected or 'none'}",
        "",
        "This vulnerability is active on your estate. Generate "
        "remediation guidance or prioritize it alongside the other "
        "open findings.",
    ]

    return "\n".join(lines)


def _render_asset_risk(ctx: dict) -> str:
    asset = ctx.get("asset") or {}
    ports = ctx.get("open_ports", [])
    findings = ctx.get("recent_findings", [])
    services = asset.get("services", [])

    lines = [
        f"### Why {asset.get('name') or 'this asset'} is risky",
        "",
        f"- **Risk score:** {asset.get('risk_score', 0)} / 100",
        f"- **Security score:** {asset.get('security_score', 0)} / 100",
        f"- **Type:** {asset.get('asset_type') or 'Unknown'} · "
        f"**IP:** {asset.get('ip_address') or 'N/A'}",
        f"- **Findings:** {asset.get('total_findings', 0)} total "
        f"(Critical {asset.get('critical', 0)}, "
        f"High {asset.get('high', 0)}, "
        f"Medium {asset.get('medium', 0)}, "
        f"Low {asset.get('low', 0)})",
        f"- **Exposure:** {len(ports)} open port(s) · "
        f"{len(services)} service(s)",
    ]

    if ports:
        lines += ["", f"**Open ports:** {', '.join(str(p) for p in ports)}"]

    if findings:
        lines += ["", "**Key findings:**"]
        for finding in findings[:5]:
            lines.append(
                f"- **{finding.get('severity', '')}** "
                f"{finding.get('cve') or finding.get('title', '?')} — "
                f"{finding.get('status', '')}"
            )

    lines += [
        "",
        "**Recommendation:** close unused ports, patch the findings above, "
        "and restrict exposure to bring the risk score down.",
    ]

    return "\n".join(lines)


def _render_scan_summary(ctx: dict) -> str:
    by_status = ctx.get("by_status", {})
    scans = ctx.get("scans", [])
    date_label = ctx.get("date", datetime.now(UTC).date().isoformat())

    lines = [
        f"### Today's Scans — {date_label}",
        "",
        f"- **Total scans:** {ctx.get('total', 0)}",
        f"- **Completed:** {by_status.get('COMPLETED', 0)}",
        f"- **Running:** {by_status.get('RUNNING', 0)}",
        f"- **Pending:** {by_status.get('PENDING', 0)}",
        f"- **Failed:** {by_status.get('FAILED', 0)}",
    ]

    if scans:
        lines += ["", "| Asset | Status | Findings | Started |", "| --- | --- | --- | --- |"]
        for scan in scans:
            lines.append(
                f"| {scan.get('asset_name', '?')} | "
                f"{scan.get('status', '')} | "
                f"{scan.get('finding_count', 0)} | "
                f"{_fmt_datetime(scan.get('started_at'))} |"
            )

    if not scans:
        lines += ["", "No scans were started today."]

    lines += [
        "",
        "Run scans against uncovered assets to keep the baseline current.",
    ]

    return "\n".join(lines)


def _render_asset_summary(ctx: dict) -> str:
    overview = ctx.get("overview", {})
    by_type = ctx.get("by_type", {})
    by_environment = ctx.get("by_environment", {})
    top_assets = ctx.get("top_assets", [])

    lines = [
        "### Asset Estate Summary",
        "",
        f"- **Total assets:** {ctx.get('total', 0)}",
        f"- **Findings:** {overview.get('total_findings', 0)} total "
        f"(Critical {overview.get('critical_findings', 0)}, "
        f"High {overview.get('high_findings', 0)}, "
        f"Medium {overview.get('medium_findings', 0)}, "
        f"Low {overview.get('low_findings', 0)})",
        f"- **Risk score:** {overview.get('risk_score', 0)} / 100",
    ]

    if by_type:
        lines += ["", "**By type:**"]
        for asset_type, count in sorted(
            by_type.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            lines.append(f"- {asset_type}: {count}")

    if by_environment:
        lines += ["", "**By environment:**"]
        for environment, count in sorted(
            by_environment.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            lines.append(f"- {environment}: {count}")

    if top_assets:
        lines += ["", "**Most exposed assets:**"]
        for asset in top_assets[:5]:
            lines.append(
                f"- **{asset.get('asset_name', '?')}** — risk "
                f"{asset.get('risk_score', 0)} / 100, "
                f"{asset.get('total_findings', 0)} findings"
            )

    lines += [
        "",
        "Keep scan coverage current across the estate and focus "
        "remediation on the most exposed assets above.",
    ]

    return "\n".join(lines)


def _render_remediation(ctx: dict) -> str:
    finding = ctx.get("finding") or {}

    if not finding:
        return (
            "### Remediation\n\n"
            "I could not resolve a specific finding to remediate. "
            "Reference a finding id, a CVE, or an asset name in your "
            "request."
        )

    recommendation = (finding.get("recommendation") or "").strip()

    title = finding.get("title") or finding.get("cve") or "Finding"
    cve = finding.get("cve")

    header = f"### Remediation — {title}"
    if cve and cve not in title:
        header += f" ({cve})"

    lines = [
        header,
        "",
        f"- **Severity:** {finding.get('severity', 'UNKNOWN')} · "
        f"**CVSS:** {_fmt_cvss(finding.get('cvss'))}",
        f"- **Affected asset:** {finding.get('affected_asset') or '-'} · "
        f"**Service:** {finding.get('affected_service') or '-'}",
        f"- **Status:** {finding.get('status', 'OPEN')}",
    ]

    if cve:
        lines.append(f"- **CVE:** {cve}")

    description = (finding.get("description") or "").strip()
    if description:
        lines += ["", f"**Description:** {description}"]

    lines += ["", "**Recommended actions:**"]
    if recommendation and recommendation.lower() not in (
        "update to the latest supported version.",
    ):
        lines.append(f"- {recommendation}")

    lines += [
        "- Update the affected product to the latest patched version.",
        "- Apply vendor mitigation if a patch is not yet available.",
        "- Re-scan the asset and close the finding once verified.",
        "- Review exposure and network segmentation to limit impact.",
    ]

    return "\n".join(lines)


def _render_prioritize(ctx: dict) -> str:
    overview = ctx.get("overview", {})
    findings = ctx.get("findings", [])
    top_assets = ctx.get("top_assets", [])

    lines = [
        "### Vulnerability Prioritization",
        "",
        f"- **Risk score:** {overview.get('risk_score', 0)} / 100",
        f"- **Findings:** {overview.get('total_findings', 0)} total "
        f"(Critical {overview.get('critical_findings', 0)}, "
        f"High {overview.get('high_findings', 0)}, "
        f"Medium {overview.get('medium_findings', 0)}, "
        f"Low {overview.get('low_findings', 0)})",
    ]

    if findings:
        lines += ["", "**Priority order (by severity, then CVSS):**"]
        for index, finding in enumerate(findings[:10], start=1):
            lines.append(
                f"{index}. **{finding.get('severity', '')}** "
                f"{finding.get('cve') or finding.get('title', '?')} — "
                f"CVSS {_fmt_cvss(finding.get('cvss'))} — "
                f"{finding.get('asset_name', '?')} ({finding.get('status', '')})"
            )

    if top_assets:
        lines += ["", "**Most exposed assets:**"]
        for asset in top_assets[:5]:
            lines.append(
                f"- **{asset.get('asset_name', '?')}** — risk "
                f"{asset.get('risk_score', 0)} / 100, "
                f"{asset.get('total_findings', 0)} findings"
            )

    lines += [
        "",
        "Start remediation with the critical/high items, then work down by "
        "CVSS while tracking affected assets.",
    ]

    return "\n".join(lines)


def _render_executive_summary(ctx: dict) -> str:
    overview = ctx.get("overview", {})
    top_assets = ctx.get("top_assets", [])

    posture = overview.get("risk_score", 0)
    if posture >= 75:
        level = "Critical"
    elif posture >= 50:
        level = "High"
    elif posture >= 25:
        level = "Medium"
    else:
        level = "Low"

    lines = [
        "### Executive Security Summary",
        "",
        f"**Posture:** {level} risk (score {posture}/100) as of "
        f"{datetime.now(UTC).strftime('%Y-%m-%d')}.",
        "",
        f"- **Assets monitored:** {overview.get('assets', 0)}",
        f"- **Scans completed:** {overview.get('completed_scans', 0)}",
        f"- **Total findings:** {overview.get('total_findings', 0)} "
        f"(Critical {overview.get('critical_findings', 0)}, "
        f"High {overview.get('high_findings', 0)})",
        f"- **Attack surface:** {overview.get('open_ports', 0)} open "
        f"ports · {overview.get('total_services', 0)} services",
    ]

    if top_assets:
        lines += ["", "**Priority assets:**"]
        for asset in top_assets[:3]:
            lines.append(
                f"- {asset.get('asset_name', '?')} — "
                f"{asset.get('total_findings', 0)} findings, "
                f"{asset.get('critical_findings', 0)} critical"
            )

    lines += [
        "",
        "**Next steps:** prioritize remediation of critical and high "
        "findings, keep scan coverage current, and reduce exposed ports.",
    ]

    return "\n".join(lines)


def _render_general(ctx: dict) -> str:
    return (
        "### GuardianX Security Copilot\n\n"
        "I can help with the following:\n\n"
        "1. **Explain a CVE** — reference a CVE identifier.\n"
        "2. **Explain a vulnerability** — reference a finding id, CVE or "
        "asset name.\n"
        "3. **Why is this asset risky?** — name an asset or pass its id.\n"
        "4. **Summarize today's scans** — scan activity and findings.\n"
        "5. **Summarize assets** — estate overview by type and exposure.\n"
        "6. **Generate remediation** — remediation steps for a finding, "
        "CVE or asset.\n"
        "7. **Prioritize vulnerabilities** — ordered by severity and CVSS.\n"
        "8. **Generate executive summary** — board-ready posture overview.\n"
        "9. **Security recommendations** — prioritized hardening actions "
        "for your estate.\n\n"
        "Try one of the quick actions above, or describe your request in "
        "plain language."
    )


def _render_explain_vulnerability(ctx: dict) -> str:
    finding = ctx.get("finding") or {}

    if not finding:
        return (
            "### Vulnerability Explanation\n\n"
            "I could not resolve a specific vulnerability to explain. "
            "Reference a finding id, a CVE, or an asset name in your "
            "request."
        )

    title = finding.get("title") or finding.get("cve") or "Vulnerability"
    cve = finding.get("cve")
    description = (finding.get("description") or "").strip()

    header = f"### {title}"
    if cve and cve not in title:
        header += f" ({cve})"

    lines = [
        header,
        "",
        f"- **Severity:** {finding.get('severity', 'UNKNOWN')} · "
        f"**CVSS:** {_fmt_cvss(finding.get('cvss'))}",
        f"- **Affected asset:** {finding.get('affected_asset') or '-'} · "
        f"**Service:** {finding.get('affected_service') or '-'}",
        f"- **Status:** {finding.get('status', 'OPEN')}",
    ]

    if cve:
        lines.append(f"- **CVE:** {cve}")

    if description:
        lines += ["", f"**What it is:** {description}"]

    lines += [
        "",
        "**What it means for you:** this vulnerability is active on the "
        "asset above. If exploited, it can weaken confidentiality, "
        "integrity or availability depending on the severity and CVSS "
        "score. Treat it according to its severity and close it as part of "
        "your remediation cycle.",
    ]

    return "\n".join(lines)


def _render_technical_summary(ctx: dict) -> str:
    overview = ctx.get("overview", {})
    findings = ctx.get("findings", [])

    lines = [
        "### Technical Security Summary",
        "",
        f"- **Estate:** {overview.get('assets', 0)} asset(s) · "
        f"{overview.get('open_ports', 0)} open port(s) · "
        f"{overview.get('total_services', 0)} service(s)",
        f"- **Findings:** {overview.get('total_findings', 0)} total "
        f"(Critical {overview.get('critical_findings', 0)}, "
        f"High {overview.get('high_findings', 0)}, "
        f"Medium {overview.get('medium_findings', 0)})",
    ]

    if findings:
        lines += [
            "",
            "| Severity | CVE | Finding | Asset | CVSS | EPSS | KEV |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for finding in findings[:10]:
            epss = finding.get("epss_score")
            epss_text = (
                f"{round(epss * 100)}%"
                if epss is not None
                else "-"
            )
            kev_text = (
                "Yes"
                if finding.get("exploited")
                else "No"
            )
            lines.append(
                f"| {finding.get('severity', '')} | "
                f"{finding.get('cve') or '-'} | "
                f"{finding.get('title', '')} | "
                f"{finding.get('asset_name', '?')} | "
                f"{_fmt_cvss(finding.get('cvss'))} | "
                f"{epss_text} | {kev_text} |"
            )

    fixes = [
        finding.get("recommendation")
        for finding in findings
        if finding.get("recommendation")
    ]
    if fixes:
        lines += ["", "**Recommended fixes:**"]
        seen = set()
        for fix in fixes:
            key = fix.lower()
            if key not in seen:
                seen.add(key)
                lines.append(f"- {fix}")

    lines += [
        "",
        "**Affected assets:** the findings above map to the scanned assets "
        "listed in the table; remediate the critical/high rows first.",
    ]

    return "\n".join(lines)


def _render_dashboard_insights(ctx: dict) -> str:
    overview = ctx.get("overview", {})
    top_vulnerabilities = ctx.get("top_vulnerabilities", [])
    top_assets = ctx.get("top_vulnerable_assets", [])
    risk_trend = ctx.get("risk_trend", [])
    findings_trend = ctx.get("findings_trend", [])
    asset_distribution = ctx.get("asset_distribution", [])

    lines = [
        "### Dashboard Insights",
        "",
        f"- **Posture:** risk {overview.get('risk_score', 0)} / 100 · "
        f"{overview.get('assets', 0)} assets · "
        f"{overview.get('total_findings', 0)} findings",
        f"- **Attack surface:** {overview.get('open_ports', 0)} open "
        f"port(s) · {overview.get('total_services', 0)} service(s)",
    ]

    if top_vulnerabilities:
        lines += ["", "**Top 5 risks:**"]
        for index, vuln in enumerate(top_vulnerabilities[:5], start=1):
            lines.append(
                f"{index}. **{vuln.get('severity', '')}** "
                f"{vuln.get('cve') or vuln.get('title', '?')} — "
                f"CVSS {_fmt_cvss(vuln.get('cvss'))} — "
                f"{vuln.get('asset', '?')}"
            )

    if top_assets:
        lines += ["", "**Most vulnerable assets:**"]
        for asset in top_assets[:5]:
            lines.append(
                f"- **{asset.get('asset_name', '?')}** — "
                f"{asset.get('total_findings', 0)} findings, "
                f"{asset.get('critical_findings', 0)} critical"
            )

    if asset_distribution:
        lines += ["", "**Asset distribution:**"]
        for entry in asset_distribution[:5]:
            lines.append(
                f"- {entry.get('type', '?')}: {entry.get('count', 0)}"
            )

    if risk_trend:
        recent = [point.get("score", 0) for point in risk_trend[-7:]]
        first = recent[0]
        last = recent[-1]
        direction = (
            "improving"
            if last < first
            else "worsening"
            if last > first
            else "stable"
        )
        lines.append(
            "",
        )
        lines.append(
            f"**Trend:** risk is **{direction}** over the last 7 days "
            f"({first} → {last} / 100).",
        )

    if findings_trend:
        recent_findings = [
            point.get("critical", 0) + point.get("high", 0)
            for point in findings_trend[-7:]
        ]
        new_critical_high = sum(recent_findings)
        lines.append(
            f"- {new_critical_high} critical/high finding(s) appeared in "
            "the last 7 days."
        )

    lines += [
        "",
        "**Improvement suggestions:**",
        "- Remediate critical and high findings before they accumulate.",
        "- Reduce the exposed attack surface (close unused ports/services).",
        "- Keep scan coverage current across all assets.",
        "- Track critical/high trends weekly and enforce SLAs by severity.",
    ]

    return "\n".join(lines)


def _render_threat_summary(ctx: dict) -> str:
    cve_id = ctx.get("cve") or "the referenced CVE"
    nvd = ctx.get("nvd") or {}
    vt = ctx.get("virustotal")

    lines = [
        f"### Threat Summary — {cve_id}",
        "",
    ]

    if not ctx.get("epss_score") and not nvd:
        lines.append(
            "External intelligence sources were unreachable or returned "
            "no data for this CVE. Check the threat intelligence source "
            "status and retry."
        )
        if vt:
            lines += [
                "",
                "**VirusTotal (asset IOC):**",
                f"- **Risk:** {vt.get('risk_score')} · "
                f"{vt.get('threat_level', 'unknown')}",
                f"- **Detections:** {vt.get('detection_ratio', '-')} "
                f"({vt.get('resource', '')})",
            ]
        return "\n".join(lines)

    if nvd:
        lines += [
            f"**Vulnerability (NVD):** {nvd.get('title') or cve_id}",
            f"- **Severity:** {nvd.get('severity', 'UNKNOWN')} · "
            f"**CVSS:** {_fmt_cvss(nvd.get('cvss_score'))}",
        ]
        if nvd.get("description"):
            lines.append(f"- **Description:** {nvd.get('description')}")

    lines += ["", "**Exploitation intelligence:**"]

    epss = ctx.get("epss_score")
    if epss is not None:
        percentile = ctx.get("epss_percentile")
        lines.append(
            f"- **EPSS:** {round(epss * 100)}% exploitation probability"
            + (
                f" · {round(percentile * 100)}th percentile"
                if percentile is not None
                else ""
            )
        )
    else:
        lines.append("- **EPSS:** not available")

    if ctx.get("exploited"):
        lines.append(
            f"- **CISA KEV:** actively exploited (due {ctx.get('kev_due_date') or 'n/a'})"
        )
    else:
        lines.append("- **CISA KEV:** no known active exploitation")

    techniques = ctx.get("attack_techniques", [])
    if techniques:
        lines += ["", "**MITRE ATT&CK:**"]
        for technique in techniques[:6]:
            lines.append(
                f"- **{technique.get('id', '')}** "
                f"{technique.get('name', '')} — "
                f"{', '.join(technique.get('tactics', []))}"
            )

    if ctx.get("guardianx_risk_score") is not None:
        lines.append("")
        lines.append(
            f"**GuardianX composite risk:** "
            f"{ctx.get('guardianx_risk_score')} / 100 "
            f"({ctx.get('threat_level', 'UNKNOWN')}).",
        )

    if vt:
        lines += [
            "",
            "**VirusTotal (asset IOC):**",
            f"- **Risk:** {vt.get('risk_score')} · "
            f"{vt.get('threat_level', 'unknown')}",
            f"- **Detections:** {vt.get('detection_ratio', '-')} "
            f"({vt.get('resource', '')})",
        ]

    lines += [
        "",
        "**Conclusion:** prioritize this CVE according to the composite "
        "risk, KEV status and EPSS probability above, and apply the "
        "vendor fixes referenced in the advisories.",
    ]

    return "\n".join(lines)


def _render_natural_language_search(ctx: dict) -> str:
    query = ctx.get("query", "")
    parsed = ctx.get("parsed", {})
    findings = ctx.get("findings", [])
    assets = ctx.get("assets", [])
    services = ctx.get("services", [])

    predicates = []
    if parsed.get("severity"):
        predicates.append(f"severity={parsed['severity']}")
    if parsed.get("service"):
        predicates.append(f"service={parsed['service']}")
    if parsed.get("port"):
        predicates.append(f"port={parsed['port']}")
    if parsed.get("asset_type"):
        predicates.append(f"type={parsed['asset_type']}")
    if parsed.get("cve"):
        predicates.append(f"cve={parsed['cve']}")
    if parsed.get("exposed"):
        predicates.append("exposed")

    lines = [
        "### Natural Language Search",
        "",
        f"Query: **{query}**",
    ]

    if predicates:
        lines.append(f"Resolved as: `{', '.join(predicates)}`")

    total = len(findings) + len(assets) + len(services)
    lines.append("")
    lines.append(f"**{total} match(es) found.**")

    if findings:
        lines += ["", "**Findings:**"]
        for finding in findings[:10]:
            lines.append(
                f"- **{finding.get('severity', '')}** "
                f"{finding.get('cve') or finding.get('title', '?')} — "
                f"{finding.get('asset', '?')} "
                f"({finding.get('service') or 'unknown service'})"
            )

    if assets:
        lines += ["", "**Assets:**"]
        for asset in assets[:10]:
            lines.append(
                f"- **{asset.get('name', '?')}** — "
                f"{asset.get('asset_type', '')} "
                f"({asset.get('ip_address') or asset.get('domain') or 'no address'})"
            )

    if services:
        lines += ["", "**Services:**"]
        for service in services[:10]:
            lines.append(
                f"- {service.get('service') or '?'} "
                f"({service.get('port')}/{service.get('protocol', 'tcp')}) "
                f"on {service.get('asset', '?')}"
            )

    if total == 0:
        lines += [
            "",
            "No assets, findings, or services matched. Try a broader query "
            "such as a different severity, service name, or 'show all "
            "assets'.",
        ]

    return "\n".join(lines)


def _render_security_recommendations(ctx: dict) -> str:
    overview = ctx.get("overview", {})
    findings = ctx.get("findings", [])
    top_assets = ctx.get("top_assets", [])

    critical = overview.get("critical_findings", 0)
    high = overview.get("high_findings", 0)
    medium = overview.get("medium_findings", 0)

    lines = [
        "### Security Recommendations",
        "",
        f"Based on your estate: {overview.get('assets', 0)} asset(s), "
        f"{overview.get('total_findings', 0)} finding(s) "
        f"(Critical {critical}, High {high}, Medium {medium}), "
        f"{overview.get('open_ports', 0)} open port(s) and "
        f"{overview.get('total_services', 0)} service(s).",
        "",
        "**Quick wins (this week):**",
    ]

    if critical or high:
        lines.append(
            "- Remediate critical and high severity findings first; "
            "prioritize by CVSS and internet exposure."
        )
    else:
        lines.append(
            "- No critical or high findings right now; keep the current "
            "patch cadence."
        )

    if medium:
        lines.append(
            f"- Schedule remediation for the {medium} medium severity "
            "findings to keep the backlog from growing."
        )

    if overview.get("open_ports", 0):
        lines.append(
            "- Review open ports and services; close anything not required "
            "for business operations."
        )

    lines.append(
        "- Keep scan coverage current across all assets so new exposure "
        "is caught early."
    )

    if top_assets:
        lines += ["", "**Focus areas:**"]
        for asset in top_assets[:5]:
            lines.append(
                f"- **{asset.get('asset_name', '?')}** — "
                f"{asset.get('total_findings', 0)} findings, "
                f"{asset.get('risk_score', 0)}/100 risk"
            )

    lines += [
        "",
        "**Longer-term:**",
        "- Enforce vulnerability management SLAs by severity.",
        "- Reduce internet-facing attack surface and apply network "
        "segmentation.",
        "- Track remediation debt and exposure trends over time.",
    ]

    return "\n".join(lines)


_RENDERERS = {
    CopilotIntent.EXPLAIN_CVE: _render_explain_cve,
    CopilotIntent.EXPLAIN_VULNERABILITY: _render_explain_vulnerability,
    CopilotIntent.ASSET_RISK: _render_asset_risk,
    CopilotIntent.SCAN_SUMMARY: _render_scan_summary,
    CopilotIntent.ASSET_SUMMARY: _render_asset_summary,
    CopilotIntent.REMEDIATION: _render_remediation,
    CopilotIntent.PRIORITIZE: _render_prioritize,
    CopilotIntent.EXECUTIVE_SUMMARY: _render_executive_summary,
    CopilotIntent.TECHNICAL_SUMMARY: _render_technical_summary,
    CopilotIntent.DASHBOARD_INSIGHTS: _render_dashboard_insights,
    CopilotIntent.THREAT_SUMMARY: _render_threat_summary,
    CopilotIntent.NATURAL_LANGUAGE_SEARCH: _render_natural_language_search,
    CopilotIntent.SECURITY_RECOMMENDATIONS: _render_security_recommendations,
    CopilotIntent.GENERAL: _render_general,
}


class RulesProvider(BaseCopilotProvider):
    """
    Built-in deterministic provider. Answers are rendered from the live
    database context and require no external AI service.
    """

    name = "rules"

    def __init__(self) -> None:
        self.model = None

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        context: dict | None = None,
    ) -> str:
        ctx = context or {}
        intent = ctx.get("intent", CopilotIntent.GENERAL)
        renderer = _RENDERERS.get(intent, _render_general)
        return renderer(ctx)
