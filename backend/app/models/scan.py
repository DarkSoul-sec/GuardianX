from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.scan_status import ScanStatus
from app.database.base import Base


class Scan(Base):
    __tablename__ = "scans"

    __table_args__ = (
        Index("ix_scans_status", "status"),
        Index("ix_scans_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(
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

    status: Mapped[ScanStatus] = mapped_column(
        Enum(
            ScanStatus,
            name="scan_status",
        ),
        default=ScanStatus.PENDING,
        nullable=False,
    )

    scanner: Mapped[str] = mapped_column(
        String(50),
        default="nmap",
        nullable=False,
    )

    scan_profile: Mapped[str] = mapped_column(
        String(20),
        default="standard",
        nullable=False,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    asset = relationship(
        "Asset",
        back_populates="scans",
    )

    results = relationship(
        "ScanResult",
        back_populates="scan",
        cascade="all, delete-orphan",
    )
