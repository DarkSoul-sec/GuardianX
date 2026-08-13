"""
Risk scoring utilities.

This module contains the canonical implementation of GuardianX's
risk score calculation.

Every service that needs a risk score should import it from here.
"""

from __future__ import annotations


def calculate_risk_score(
    critical: int,
    high: int,
    medium: int,
    low: int,
) -> int:
    """
    Calculate a simple explainable risk score.

    Current weights:

    Critical = 10
    High = 5
    Medium = 2
    Low = 1

    The score is capped at 100.
    """

    weighted_total = (
        (critical * 10)
        + (high * 5)
        + (medium * 2)
        + (low * 1)
    )

    return min(100, weighted_total)
