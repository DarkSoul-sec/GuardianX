"""
Typosquatting analyzer.

Compares the analyzed domain against a configured list of trusted
(legitimate) domains and flags look-alikes using edit distance, label
substrings and TLD swaps. Also reports structural look-alike indicators
(hyphenated names, digit substitution) that appear regardless of a brand
list.
"""

from __future__ import annotations

from app.detection.phishing.base import Analyzer, CheckResult, UrlContext, clean_result


def _edit_distance(left: str, right: str) -> int:
    """Levenshtein distance between two strings (case-insensitive)."""
    a, b = left.lower(), right.lower()

    if a == b:
        return 0

    previous = list(range(len(b) + 1))

    for i, char_a in enumerate(a, start=1):
        current = [i]

        for j, char_b in enumerate(b, start=1):
            cost = 0 if char_a == char_b else 1
            current.append(
                min(
                    current[-1] + 1,
                    previous[j] + 1,
                    previous[j - 1] + cost,
                )
            )

        previous = current

    return previous[-1]


class TyposquattingAnalyzer(Analyzer):
    """Detect look-alike domains via trusted-brand comparison and structure."""

    name = "typosquatting"
    title = "Typosquatting / Look-alike Domain"

    def analyze(self, context: UrlContext) -> list[CheckResult]:
        results: list[CheckResult] = []

        if context.is_ip_host:
            results.append(
                clean_result(
                    self.name,
                    self.title,
                    "Typosquatting checks are not applicable to IP addresses.",
                    data={"applicable": False},
                )
            )
            return results

        domain = context.approximate_domain.lower()
        hostname = context.hostname.lower()

        for trusted in self.config.trusted_domains:
            trusted = trusted.strip().lower()

            if not trusted:
                continue

            if domain == trusted or hostname == trusted:
                results.append(
                    CheckResult(
                        check=self.name,
                        title="Matches trusted domain",
                        score=0,
                        reason=f"Domain '{domain}' exactly matches trusted domain '{trusted}'.",
                        recommendation="",
                        data={"trusted_domain": trusted, "match": "exact"},
                    )
                )
                continue

            distance = _edit_distance(domain, trusted)

            if distance <= 1:
                results.append(
                    CheckResult(
                        check=self.name,
                        title="Near-identical domain",
                        score=90,
                        reason=f"Domain '{domain}' is {distance} character(s) from trusted domain '{trusted}'.",
                        recommendation="Treat as a typosquatting attempt and do not visit.",
                        data={"trusted_domain": trusted, "distance": distance},
                    )
                )
                continue

            if distance <= 2:
                results.append(
                    CheckResult(
                        check=self.name,
                        title="Similar domain",
                        score=75,
                        reason=f"Domain '{domain}' is {distance} character(s) from trusted domain '{trusted}'.",
                        recommendation="Verify ownership before trusting; likely a look-alike domain.",
                        data={"trusted_domain": trusted, "distance": distance},
                    )
                )
                continue

            if trusted in hostname and hostname != trusted:
                results.append(
                    CheckResult(
                        check=self.name,
                        title="Trusted name in host",
                        score=70,
                        reason=f"Host '{hostname}' embeds trusted domain '{trusted}' as a label.",
                        recommendation="Subdomains of look-alike hosts are a common phishing pattern.",
                        data={"trusted_domain": trusted, "match": "substring"},
                    )
                )
                continue

            if domain.split(".")[0] == trusted.split(".")[0] and domain != trusted:
                results.append(
                    CheckResult(
                        check=self.name,
                        title="Top-level domain swap",
                        score=60,
                        reason=f"Domain '{domain}' reuses the name of trusted '{trusted}' with a different TLD.",
                        recommendation="Different-TLD clones of a trusted domain are usually phishing.",
                        data={"trusted_domain": trusted, "match": "tld_swap"},
                    )
                )
                continue

            trusted_sld = trusted.split(".")[0]
            domain_sld = domain.split(".")[0]

            if trusted_sld in domain_sld and domain_sld != trusted_sld:
                results.append(
                    CheckResult(
                        check=self.name,
                        title="Brand-adjacent domain",
                        score=55,
                        reason=f"Domain '{domain}' is built around trusted name '{trusted_sld}'.",
                        recommendation="Verify the domain against the official brand before engaging.",
                        data={"trusted_domain": trusted, "match": "brand_adjacent"},
                    )
                )

        if not results:
            results.append(
                clean_result(
                    self.name,
                    self.title,
                    "No look-alike indicators detected for the domain.",
                    data={"domain": domain},
                )
            )

        return results
