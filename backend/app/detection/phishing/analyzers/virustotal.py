"""
VirusTotal reputation analyzer.

Reuses the existing GuardianX VirusTotal integration
(:mod:`app.integrations.virustotal`) to score the URL against the VirusTotal
vendor engine pool. If VirusTotal is unconfigured or unreachable the check
reports a neutral "unavailable" result instead of failing the analysis.
"""

from __future__ import annotations

from app.detection.phishing.base import Analyzer, CheckResult, UrlContext
from app.integrations.virustotal import lookup_url
from app.integrations.virustotal.exceptions import VirusTotalError


class VirusTotalAnalyzer(Analyzer):
    """Score the URL based on its VirusTotal reputation."""

    name = "virustotal"
    title = "VirusTotal Reputation"

    def __init__(self, config, api_key: str | None = None) -> None:
        super().__init__(config)
        self.api_key = api_key

    def analyze(self, context: UrlContext) -> list[CheckResult]:
        if not self.api_key:
            return [
                CheckResult(
                    check=self.name,
                    title="VirusTotal not configured",
                    score=25,
                    reason="VirusTotal is not configured. Add your API key in Settings.",
                    recommendation="Connect your VirusTotal API key to enable reputation checks.",
                    data={"available": False, "code": "virustotal_not_configured"},
                )
            ]

        try:
            report = lookup_url(self.api_key, context.raw_url)
        except VirusTotalError as exc:
            return [
                CheckResult(
                    check=self.name,
                    title="VirusTotal unavailable",
                    score=25,
                    reason="VirusTotal data is unavailable at this time.",
                    recommendation="Check the VirusTotal API configuration or re-run the analysis.",
                    data={"available": False, "code": exc.code},
                )
            ]

        if not report.found:
            return [
                CheckResult(
                    check=self.name,
                    title="Unknown VirusTotal reputation",
                    score=40,
                    reason="The URL has not been seen by VirusTotal, so its reputation is unknown.",
                    recommendation="Submit the URL to VirusTotal for a first-time analysis.",
                    data={"found": False, "permalink": report.permalink},
                )
            ]

        malicious = report.malicious
        suspicious = report.suspicious
        total = report.total

        if malicious >= 3 or (total > 0 and malicious / max(total, 1) >= 0.1):
            score = 90
            reason = f"VirusTotal flagged the URL as malicious ({malicious}/{total} engines)."
            recommendation = "Block the URL and investigate any users who may have visited it."
        elif malicious >= 1:
            score = 75
            reason = f"VirusTotal reported malicious verdicts from {malicious} engine(s)."
            recommendation = "Treat the URL as malicious and block it."
        elif suspicious >= 1:
            score = 55
            reason = f"VirusTotal reported suspicious verdicts from {suspicious} engine(s)."
            recommendation = "Investigate the URL before allowing access."
        else:
            score = 0
            reason = f"VirusTotal found no malicious or suspicious verdicts ({malicious}/{total} engines)."
            recommendation = "No action needed based on VirusTotal."

        return [
            CheckResult(
                check=self.name,
                title="VirusTotal verdict",
                score=score,
                reason=reason,
                recommendation=recommendation,
                data={
                    "available": True,
                    "found": True,
                    "detection_ratio": report.detection_ratio,
                    "malicious": report.malicious,
                    "suspicious": report.suspicious,
                    "total": report.total,
                    "threat_category": report.threat_category,
                    "reputation": report.reputation,
                    "permalink": report.permalink,
                },
            )
        ]
