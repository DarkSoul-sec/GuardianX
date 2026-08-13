"""create findings table

Revision ID: c04632ea92eb
Revises: 475262f5e297
Create Date: 2026-07-19 21:39:18.329454

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c04632ea92eb'
down_revision: Union[str, Sequence[str], None] = '475262f5e297'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "findings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scan_result_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("cpe", sa.String(length=255), nullable=True),
        sa.Column("cve", sa.String(length=50), nullable=True),
        sa.Column("cvss", sa.Float(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["scan_result_id"],
            ["scan_results.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_findings_id"),
        "findings",
        ["id"],
        unique=False,
    )

    op.drop_constraint(op.f('assets_created_by_fkey'), 'assets', type_='foreignkey')
    op.create_foreign_key(None, 'assets', 'users', ['created_by'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f("ix_findings_id"),
        table_name="findings",
    )

    op.drop_table("findings")
    # ### end Alembic commands ###
