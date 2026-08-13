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


class ScheduledScan(Base):
    __tablename__ = "scheduled_scans"

    __table_args__ = (
        Index("ix_scheduled_scans_enabled_next_run", "enabled", "next_run_at"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    asset_id: Mapped[int] = mapped_column(
        ForeignKey(
            "assets.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    scanner: Mapped[str] = mapped_column(
        String(50),
        default="nmap",
        nullable=False,
    )

    cadence: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    time_of_day: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
    )

    week_day: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    month_day: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    asset = relationship(
        "Asset",
    )
