"""
Per-user threat intelligence search history.

Every IOC lookup is recorded as a row here so analysts can review recent
searches, re-run them, and understand which indicators were flagged. The
full VirusTotal report is served from the in-process 24-hour cache; only the
verdict summary is persisted, keeping history lightweight and privacy-safe.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class IntelligenceSearch(Base):
    __tablename__ = "intelligence_searches"

    __table_args__ = (
        Index(
            "ix_intelligence_searches_user_created",
            "user_id",
            "created_at",
        ),
        Index(
            "ix_intelligence_searches_user_type",
            "user_id",
            "resource_type",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    resource_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    resource: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )

    threat_level: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="unknown",
    )

    risk_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    reputation: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    detected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    malicious: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    suspicious: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    harmless: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    undetected: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    detection_ratio: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="0/0",
    )

    threat_category: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="intelligence_searches",
    )
