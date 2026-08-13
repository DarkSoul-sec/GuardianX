from datetime import date

from sqlalchemy import Date, Float, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class CveEpssHistory(Base):
    """Daily EPSS snapshots per CVE.

    EPSS scores change daily; this table keeps a rolling history so the UI can
    render an exploitation-likelihood trend for a vulnerability. One row per
    CVE per day, captured whenever a CVE is enriched.
    """

    __tablename__ = "cve_epss_history"

    __table_args__ = (
        UniqueConstraint("cve_id", "recorded_on", name="uq_cve_epss_daily"),
        Index("ix_cve_epss_history_cve_id", "cve_id"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    cve_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    percentile: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    recorded_on: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
