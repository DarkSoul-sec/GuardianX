"""Persistent daily EPSS snapshots.

EPSS is a point-in-time score that FIRST republishes daily. Capturing a
snapshot each time a CVE is enriched builds a rolling history that the
frontend can chart as an exploitation-likelihood trend.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.database.session import SessionLocal
from app.logger import logger
from app.models.cve_epss_history import CveEpssHistory

_MAX_POINTS = 60


def record_snapshot(
    cve_id: str,
    score: float,
    percentile: float,
) -> None:
    """Upsert today's EPSS snapshot for a CVE.

    Failures are logged and swallowed so enrichment never breaks because of a
    history write.
    """

    normalized = cve_id.strip().upper()
    today = date.today()

    try:
        with SessionLocal() as db:
            existing = db.execute(
                select(CveEpssHistory).where(
                    CveEpssHistory.cve_id == normalized,
                    CveEpssHistory.recorded_on == today,
                )
            ).scalar_one_or_none()

            if existing is not None:
                existing.score = score
                existing.percentile = percentile
            else:
                db.add(
                    CveEpssHistory(
                        cve_id=normalized,
                        score=score,
                        percentile=percentile,
                        recorded_on=today,
                    )
                )

            db.commit()
    except Exception:
        logger.warning(
            "[INTELLIGENCE] Failed to record EPSS snapshot for %s",
            normalized,
            exc_info=True,
        )


def get_history(
    cve_id: str,
    limit: int = 14,
) -> list[dict]:
    """Most recent EPSS snapshots for a CVE, newest first."""

    normalized = cve_id.strip().upper()
    limit = max(1, min(limit, _MAX_POINTS))

    try:
        with SessionLocal() as db:
            rows = db.execute(
                select(CveEpssHistory)
                .where(CveEpssHistory.cve_id == normalized)
                .order_by(CveEpssHistory.recorded_on.desc())
                .limit(limit)
            ).scalars().all()
    except Exception:
        logger.warning(
            "[INTELLIGENCE] Failed to load EPSS history for %s",
            normalized,
            exc_info=True,
        )
        return []

    return [
        {
            "date": row.recorded_on.isoformat(),
            "score": row.score,
            "percentile": row.percentile,
        }
        for row in rows
    ]
