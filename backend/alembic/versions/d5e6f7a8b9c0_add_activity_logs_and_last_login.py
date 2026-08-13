"""add_activity_logs_and_last_login

Revision ID: d5e6f7a8b9c0
Revises: c3d4e5f6a7b8
Create Date: 2026-08-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "d5e6f7a8b9c0"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "last_login",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.create_table(
        "activity_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "action",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "entity_type",
            sa.String(length=50),
            nullable=True,
        ),
        sa.Column(
            "entity_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "detail",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "meta",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "ip_address",
            sa.String(length=64),
            nullable=True,
        ),
        sa.Column(
            "user_agent",
            sa.String(length=255),
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
        op.f("ix_activity_logs_id"),
        "activity_logs",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_activity_logs_user_id"),
        "activity_logs",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_activity_logs_action"),
        "activity_logs",
        ["action"],
        unique=False,
    )
    op.create_index(
        op.f("ix_activity_logs_created_at"),
        "activity_logs",
        ["created_at"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_activity_logs_user_id_users",
        "activity_logs",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_activity_logs_user_id_users",
        "activity_logs",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_activity_logs_created_at"),
        table_name="activity_logs",
    )
    op.drop_index(
        op.f("ix_activity_logs_action"),
        table_name="activity_logs",
    )
    op.drop_index(
        op.f("ix_activity_logs_user_id"),
        table_name="activity_logs",
    )
    op.drop_index(
        op.f("ix_activity_logs_id"),
        table_name="activity_logs",
    )
    op.drop_table("activity_logs")
    op.drop_column("users", "last_login")