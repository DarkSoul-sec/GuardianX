"""
Configurable scoring engine for phishing analysis.

Each analyzer reports a normalized 0-100 score per check. The engine weighs
each check by a configurable weight (defaulting to a 100-point budget) and
derives a threat score, a risk level, the reasons behind the verdict, and a
deduplicated recommendation list. All thresholds and weights are injected so
no detection behavior is hardcoded in the analyzers.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.detection.phishing.base import CheckResult


@dataclass(frozen=True)
class RiskThresholds:
    """Risk-level boundaries (inclusive)."""

    medium: int = 25
    high: int = 50
    critical: int = 75


def risk_level(score: int, thresholds: RiskThresholds) -> str:
    """Map a 0-100 score to a low/medium/high/critical risk level."""
    score = max(0, min(100, score))

    if score >= thresholds.critical:
        return "critical"
    if score >= thresholds.high:
        return "high"
    if score >= thresholds.medium:
        return "medium"
    return "low"


@dataclass(frozen=True)
class ScoreSummary:
    """Aggregated verdict produced by :class:`ScoreEngine`."""

    threat_score: int
    risk_level: str
    reasons: list[str]
    recommendations: list[str]
    contributions: dict[str, float]


class ScoreEngine:
    """Aggregate normalized check results into a single verdict."""

    def __init__(
        self,
        weights: dict[str, float],
        thresholds: RiskThresholds,
    ) -> None:
        self._weights = {name: float(w) for name, w in weights.items() if w > 0}
        self._thresholds = thresholds

    def aggregate(self, results: list[CheckResult]) -> ScoreSummary:
        # Only the strongest signal per check counts, so multiple findings
        # from one analyzer cannot inflate its contribution.
        grouped: dict[str, int] = {}
        for result in results:
            grouped[result.check] = max(grouped.get(result.check, 0), result.score)

        contributions: dict[str, float] = {}
        total = 0.0

        for check, score in grouped.items():
            weight = self._weights.get(check, 0.0)
            contribution = weight * (score / 100.0)
            contributions[check] = round(contribution, 2)
            total += contribution

        threat_score = int(round(min(100.0, max(0.0, total))))
        level = risk_level(threat_score, self._thresholds)

        significant = [r for r in results if r.score >= self._thresholds.medium]
        significant.sort(key=lambda r: r.score, reverse=True)

        reasons = [r.reason for r in significant]

        recommendations: list[str] = []
        seen: set[str] = set()

        for result in significant:
            if result.score < self._thresholds.high or not result.recommendation:
                continue

            text = result.recommendation.strip()

            if text and text not in seen:
                seen.add(text)
                recommendations.append(text)

        return ScoreSummary(
            threat_score=threat_score,
            risk_level=level,
            reasons=reasons,
            recommendations=recommendations,
            contributions=contributions,
        )
