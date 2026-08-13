"""add_findings_triage

Revision ID: c3f9a1e2b4d5
Revises: 9d4e6a1b2c3d
Create Date: 2026-08-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "c3f9a1e2b4d5"
down_revision: Union[str, Sequence[str], None] = "9d4e6a1b2c3d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "findings",
        sa.Column(
            "assigned_to",
            sa.Integer(),
            nullable=True,
        ),
    )
    op.create_index(
        op.f("ix_findings_assigned_to"),
        "findings",
        ["assigned_to"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_findings_assigned_to_users",
        "findings",
        "users",
        ["assigned_to"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "findings",
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "findings",
        sa.Column(
            "due_date",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.create_table(
        "finding_activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "finding_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "action",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "old_value",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "new_value",
            sa.Text(),
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
        op.f("ix_finding_activities_finding_id"),
        "finding_activities",
        ["finding_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_finding_activities_user_id"),
        "finding_activities",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_finding_activities_id"),
        "finding_activities",
        ["id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_finding_activities_finding_id_findings",
        "finding_activities",
        "findings",
        ["finding_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_finding_activities_user_id_users",
        "finding_activities",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_finding_activities_user_id_users",
        "finding_activities",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_finding_activities_finding_id_findings",
        "finding_activities",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_finding_activities_id"),
        table_name="finding_activities",
    )
    op.drop_index(
        op.f("ix_finding_activities_user_id"),
        table_name="finding_activities",
    )
    op.drop_index(
        op.f("ix_finding_activities_finding_id"),
        table_name="finding_activities",
    )
    op.drop_table("finding_activities")

    op.drop_column("findings", "due_date")
    op.drop_column("findings", "notes")
    op.drop_constraint(
        "fk_findings_assigned_to_users",
        "findings",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_findings_assigned_to"),
        table_name="findings",
    )
    op.drop_column("findings", "assigned_to")
