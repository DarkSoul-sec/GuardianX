"""
Phishing detection service.

Orchestrates the analyzer set against a validated URL, runs each analyzer
concurrently, aggregates the results through the configurable :class:`ScoreEngine`,
adds a human-readable summary, and returns a normalized
:class:`PhishingAnalysisResponse`. Individual analyzer failures degrade to
neutral low-confidence results instead of failing the whole analysis.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

from app.detection.phishing.analyzers import build_analyzers
from app.detection.phishing.base import Analyzer, CheckResult, build_url_context
from app.detection.phishing.config import PhishingConfig
from app.detection.phishing.schemas import (
    PhishingAnalysisResponse,
    PhishingCheckResult,
)
from app.detection.phishing.scoring import ScoreEngine, risk_level
from app.detection.phishing.summary import generate_phishing_summary
from app.logger import logger

_CONFIG = PhishingConfig.from_settings()
_SCORING = ScoreEngine(weights=_CONFIG.weights, thresholds=_CONFIG.thresholds)

_NO_REASON = "No significant phishing indicators were detected."
_NO_RECOMMENDATION = "The URL appears to be low risk; continue to monitor its reputation."


def _safe_run(analyzer: Analyzer, context) -> list[CheckResult]:
    """Run an analyzer and convert any unexpected failure to a neutral result."""
    try:
        return analyzer.analyze(context)
    except Exception:
        logger.warning(
            "Phishing analyzer %s failed unexpectedly.",
            analyzer.name,
            exc_info=True,
        )
        return [
            CheckResult(
                check=analyzer.name,
                title=analyzer.title,
                score=25,
                reason=f"The {analyzer.title.lower()} check could not be completed.",
                recommendation="Re-run the analysis or investigate the URL manually.",
                data={"available": False},
            )
        ]


def analyze_url(
    url: str,
    *,
    config: PhishingConfig | None = None,
    analyzers: list[Analyzer] | None = None,
    virustotal_api_key: str | None = None,
) -> PhishingAnalysisResponse:
    """Analyze a URL for phishing indicators and return the full verdict."""
    config = config or _CONFIG
    scoring = ScoreEngine(weights=config.weights, thresholds=config.thresholds)

    context = build_url_context(url)
    active_analyzers = analyzers or build_analyzers(
        config,
        virustotal_api_key=virustotal_api_key,
    )

    results = _run_analyzers(active_analyzers, context, config)

    summary = scoring.aggregate(results)

    reasons = list(summary.reasons) or [_NO_REASON]
    recommendations = list(summary.recommendations) or [_NO_RECOMMENDATION]

    checks = [
        PhishingCheckResult(
            check=result.check,
            title=result.title,
            score=result.score,
            severity=risk_level(result.score, config.thresholds),
            reason=result.reason,
            recommendation=result.recommendation,
            data=dict(result.data),
        )
        for result in results
    ]
    checks.sort(key=lambda check: check.score, reverse=True)

    ai_summary = generate_phishing_summary(
        url=context.raw_url,
        threat_score=summary.threat_score,
        risk_level=summary.risk_level,
        reasons=reasons,
        recommendations=recommendations,
        checks=[check.model_dump() for check in checks],
        enabled=config.enable_ai_summary,
    )

    return PhishingAnalysisResponse(
        url=context.raw_url,
        threat_score=summary.threat_score,
        risk_level=summary.risk_level,
        reasons=reasons,
        recommendations=recommendations,
        ai_summary=ai_summary,
        checks=checks,
        generated_at=datetime.now(UTC),
    )


def _run_analyzers(
    analyzers: list[Analyzer],
    context,
    config: PhishingConfig,
) -> list[CheckResult]:
    """Run every analyzer concurrently, bounded by per-analyzer timeouts."""
    timeout = max(config.network_timeout_seconds * 2, 20)
    results: list[CheckResult] = []

    with ThreadPoolExecutor(max_workers=len(analyzers)) as pool:
        futures = [pool.submit(_safe_run, analyzer, context) for analyzer in analyzers]

        for analyzer, future in zip(analyzers, futures):
            try:
                results.extend(future.result(timeout=timeout))
            except Exception:
                logger.warning(
                    "Phishing analyzer %s timed out.",
                    analyzer.name,
                )
                results.append(
                    CheckResult(
                        check=analyzer.name,
                        title=analyzer.title,
                        score=25,
                        reason=f"The {analyzer.title.lower()} check timed out.",
                        recommendation="Re-run the analysis or investigate the URL manually.",
                        data={"available": False},
                    )
                )

    return results
