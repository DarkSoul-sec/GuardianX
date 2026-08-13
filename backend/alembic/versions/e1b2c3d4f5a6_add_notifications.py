"""add_notifications

Revision ID: e1b2c3d4f5a6
Revises: c3f9a1e2b4d5
Create Date: 2026-08-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "e1b2c3d4f5a6"
down_revision: Union[str, Sequence[str], None] = "c3f9a1e2b4d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "notification_type",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "body",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "severity",
            sa.String(length=20),
            nullable=True,
        ),
        sa.Column(
            "finding_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "read_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        op.f("ix_notifications_user_id"),
        "notifications",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notifications_finding_id"),
        "notifications",
        ["finding_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notifications_created_at"),
        "notifications",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notifications_id"),
        "notifications",
        ["id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_notifications_user_id_users",
        "notifications",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_notifications_finding_id_findings",
        "notifications",
        "findings",
        ["finding_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_notifications_finding_id_findings",
        "notifications",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_notifications_user_id_users",
        "notifications",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_notifications_id"),
        table_name="notifications",
    )
    op.drop_index(
        op.f("ix_notifications_created_at"),
        table_name="notifications",
    )
    op.drop_index(
        op.f("ix_notifications_finding_id"),
        table_name="notifications",
    )
    op.drop_index(
        op.f("ix_notifications_user_id"),
        table_name="notifications",
    )
    op.drop_table("notifications")
