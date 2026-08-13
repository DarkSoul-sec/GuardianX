"""add_scheduled_scans

Revision ID: a7b8c9d0e1f2
Revises: e1b2c3d4f5a6
Create Date: 2026-08-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "e1b2c3d4f5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scheduled_scans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "asset_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "scanner",
            sa.String(length=50),
            nullable=False,
            server_default="nmap",
        ),
        sa.Column(
            "cadence",
            sa.String(length=10),
            nullable=False,
        ),
        sa.Column(
            "time_of_day",
            sa.String(length=5),
            nullable=False,
        ),
        sa.Column(
            "week_day",
            sa.String(length=10),
            nullable=True,
        ),
        sa.Column(
            "month_day",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "last_run_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "next_run_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_by",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        op.f("ix_scheduled_scans_id"),
        "scheduled_scans",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_scheduled_scans_asset_id"),
        "scheduled_scans",
        ["asset_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_scheduled_scans_next_run_at"),
        "scheduled_scans",
        ["next_run_at"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_scheduled_scans_asset_id_assets",
        "scheduled_scans",
        "assets",
        ["asset_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_scheduled_scans_created_by_users",
        "scheduled_scans",
        "users",
        ["created_by"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_scheduled_scans_created_by_users",
        "scheduled_scans",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_scheduled_scans_asset_id_assets",
        "scheduled_scans",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_scheduled_scans_next_run_at"),
        table_name="scheduled_scans",
    )
    op.drop_index(
        op.f("ix_scheduled_scans_asset_id"),
        table_name="scheduled_scans",
    )
    op.drop_index(
        op.f("ix_scheduled_scans_id"),
        table_name="scheduled_scans",
    )
    op.drop_table("scheduled_scans")
