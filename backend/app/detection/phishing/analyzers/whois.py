"""
WHOIS / domain-age analyzer.

Retrieves the registration date for a domain through the RDAP bootstrap
service (the modern, JSON-based replacement for WHOIS) and scores the domain
age. Freshly registered domains are heavily abused for phishing, so young
domains are penalized. IP hosts are not applicable.
"""

from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import quote

import requests

from app.detection.phishing.base import Analyzer, CheckResult, UrlContext, clean_result

_RDAP_BOOTSTRAP = "https://rdap.org/domain/{domain}"
_REGISTRATION_ACTIONS = ("registration", "registrar expiration")


class WhoIsAgeAnalyzer(Analyzer):
    """Score a domain based on its WHOIS/RDAP registration age."""

    name = "whois_age"
    title = "WHOIS / Domain Age"

    def analyze(self, context: UrlContext) -> list[CheckResult]:
        if context.is_ip_host:
            return [
                clean_result(
                    self.name,
                    self.title,
                    "WHOIS age is not applicable to an IP address.",
                    data={"applicable": False},
                )
            ]

        domain = context.approximate_domain
        registration_date = self._fetch_registration_date(domain)

        if registration_date is None:
            return [
                CheckResult(
                    check=self.name,
                    title="Domain age unknown",
                    score=25,
                    reason=f"Could not retrieve WHOIS/RDAP data for '{domain}'; the domain age is unknown.",
                    recommendation="Verify the domain registration manually through a WHOIS service.",
                    data={"available": False, "domain": domain},
                )
            ]

        age_days = max(0, (datetime.now(UTC) - registration_date).days)

        if age_days < self.config.new_domain_days:
            score = 75
            reason = (
                f"Domain '{domain}' was registered only {age_days} day(s) ago; "
                "recently registered domains are frequently used for phishing."
            )
        elif age_days < self.config.suspicious_domain_days:
            score = 45
            reason = (
                f"Domain '{domain}' is {age_days} day(s) old, younger than "
                "typical legitimate domains."
            )
        else:
            score = 0
            reason = f"Domain '{domain}' has an established registration age of {age_days} day(s)."

        recommendation = (
            "Exercise caution with newly registered domains and verify the sender."
            if score >= 45
            else "No action needed based on domain age."
        )

        return [
            CheckResult(
                check=self.name,
                title="Domain age",
                score=score,
                reason=reason,
                recommendation=recommendation,
                data={
                    "available": True,
                    "domain": domain,
                    "age_days": age_days,
                    "registration_date": registration_date.isoformat(),
                },
            )
        ]

    def _fetch_registration_date(self, domain: str) -> datetime | None:
        url = _RDAP_BOOTSTRAP.format(domain=quote(domain, safe=""))

        try:
            response = requests.get(
                url,
                headers={"Accept": "application/rdap+json, application/json"},
                timeout=self.config.network_timeout_seconds,
            )
        except requests.RequestException:
            return None

        if response.status_code != 200:
            return None

        try:
            payload = response.json()
        except ValueError:
            return None

        for event in payload.get("events", []):
            if event.get("eventAction") in _REGISTRATION_ACTIONS:
                event_date = event.get("eventDate")

                if not event_date:
                    continue

                try:
                    parsed = datetime.fromisoformat(str(event_date).replace("Z", "+00:00"))
                except ValueError:
                    continue

                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=UTC)

                return parsed.astimezone(UTC)

        return None
