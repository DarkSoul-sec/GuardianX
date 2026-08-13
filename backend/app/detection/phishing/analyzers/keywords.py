"""
Suspicious keywords analyzer.

Scans the host, path and query string for configured phishing keywords
(logins, verification, billing, delivery, etc.). The keyword list is
config-driven and can be extended per enterprise.
"""

from __future__ import annotations

from app.detection.phishing.base import Analyzer, CheckResult, UrlContext, clean_result


class SuspiciousKeywordsAnalyzer(Analyzer):
    """Score the URL based on suspicious keyword usage."""

    name = "keywords"
    title = "Suspicious Keywords"

    def analyze(self, context: UrlContext) -> list[CheckResult]:
        keywords = self.config.suspicious_keywords

        if not keywords:
            return [
                clean_result(
                    self.name,
                    self.title,
                    "No suspicious keyword list is configured.",
                    data={"configured": False},
                )
            ]

        parts = {
            "hostname": context.hostname,
            "path": context.path,
            "query": context.query,
        }

        matches: dict[str, list[str]] = {}

        for part, text in parts.items():
            lowered = text.lower()

            for keyword in keywords:
                keyword = keyword.strip().lower()

                if keyword and keyword in lowered:
                    matches.setdefault(part, []).append(keyword)

        count = sum(len(values) for values in matches.values())

        if count == 0:
            return [
                clean_result(
                    self.name,
                    self.title,
                    "No suspicious keywords found in the URL.",
                    data={"count": 0},
                )
            ]

        unique = sorted({keyword for values in matches.values() for keyword in values})

        if count >= 4:
            score = 70
        elif count >= 2:
            score = 50
        else:
            score = 35

        return [
            CheckResult(
                check=self.name,
                title="Suspicious keywords present",
                score=score,
                reason=(
                    f"Found {count} suspicious keyword(s) in the URL: "
                    f"{', '.join(unique)}."
                ),
                recommendation=(
                    "Phishing URLs embed login/account keywords; verify the destination "
                    "before entering credentials."
                ),
                data={
                    "count": count,
                    "keywords": unique,
                    "locations": {part: values for part, values in matches.items()},
                },
            )
        ]
