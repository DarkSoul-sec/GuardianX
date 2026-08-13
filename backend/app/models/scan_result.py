from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ScanResult(Base):
    findings = relationship(
    "Finding",
    back_populates="scan_result",
    cascade="all, delete-orphan",
)
    __tablename__ = "scan_results"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    scan_id: Mapped[int] = mapped_column(
        ForeignKey(
            "scans.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    port: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    protocol: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    state: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    service: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    version: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    product: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    cpe: Mapped[str | None] = mapped_column(
    Text,
    nullable=True,
    )

    is_ssl: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    scan = relationship(
        "Scan",
        back_populates="results",
    )
