"""
Per-user, per-provider integration credentials.

API keys are never stored in the ``users`` table or in plaintext; each
integration the user connects is a row here holding an encrypted copy of
their key. The ``provider`` column keeps the table reusable for future
integrations while this release only writes ``provider="virustotal"``.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class IntegrationCredential(Base):
    __tablename__ = "integration_credentials"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "provider",
            name="uq_integration_credentials_user_provider",
        ),
        Index(
            "ix_integration_credentials_user",
            "user_id",
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

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="virustotal",
    )

    encrypted_api_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="not_configured",
    )

    last_tested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    user = relationship(
        "User",
        back_populates="integration_credentials",
    )
