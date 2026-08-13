"""add_alerts_and_incidents

Revision ID: f1a2b3c4d5e6
Revises: d5e6f7a8b9c0
Create Date: 2026-08-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "a5e6f7a8b9c1"
down_revision: Union[str, Sequence[str], None] = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("alert_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("finding_id", sa.Integer(), nullable=True),
        sa.Column("asset_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    for col in ("user_id", "finding_id", "asset_id"):
        op.create_index(
            op.f(f"ix_alerts_{col}"),
            "alerts",
            [col],
            unique=False,
        )
    for col in ("status", "severity", "created_at", "id"):
        op.create_index(
            op.f(f"ix_alerts_{col}"),
            "alerts",
            [col],
            unique=False,
        )
    op.create_foreign_key(
        "fk_alerts_user_id_users",
        "alerts",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_alerts_finding_id_findings",
        "alerts",
        "findings",
        ["finding_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_alerts_asset_id_assets",
        "alerts",
        "assets",
        ["asset_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=True),
        sa.Column("alert_id", sa.Integer(), nullable=True),
        sa.Column("finding_id", sa.Integer(), nullable=True),
        sa.Column("assignee_id", sa.Integer(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
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
    for col in ("user_id", "asset_id", "alert_id", "finding_id", "assignee_id"):
        op.create_index(
            op.f(f"ix_incidents_{col}"),
            "incidents",
            [col],
            unique=False,
        )
    for col in ("status", "severity", "created_at", "id"):
        op.create_index(
            op.f(f"ix_incidents_{col}"),
            "incidents",
            [col],
            unique=False,
        )
    op.create_foreign_key(
        "fk_incidents_user_id_users",
        "incidents",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_incidents_asset_id_assets",
        "incidents",
        "assets",
        ["asset_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_incidents_alert_id_alerts",
        "incidents",
        "alerts",
        ["alert_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_incidents_finding_id_findings",
        "incidents",
        "findings",
        ["finding_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_incidents_assignee_id_users",
        "incidents",
        "users",
        ["assignee_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_table("incidents")
    op.drop_table("alerts")