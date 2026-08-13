from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.asset_types import AssetType
from app.database.base import Base


class Asset(Base):
    __tablename__ = "assets"

    __table_args__ = (
        Index("ix_assets_created_by", "created_by"),
        Index("ix_assets_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    asset_type: Mapped[AssetType] = mapped_column(
        Enum(
            AssetType,
            name="asset_type",
        ),
        nullable=False,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )

    domain: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    operating_system: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    environment: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    owner: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    criticality: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    creator = relationship(
        "User",
        back_populates="assets",
    )

    scans = relationship(
        "Scan",
        back_populates="asset",
        cascade="all, delete-orphan",
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
