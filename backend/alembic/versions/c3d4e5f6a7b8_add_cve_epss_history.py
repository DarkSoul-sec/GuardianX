"""add cve_epss_history table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Track daily EPSS snapshots so exploitation trends can be charted."""
    op.create_table(
        'cve_epss_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cve_id', sa.String(length=50), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('percentile', sa.Float(), nullable=False),
        sa.Column('recorded_on', sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cve_id', 'recorded_on', name='uq_cve_epss_daily'),
    )
    op.create_index(
        op.f('ix_cve_epss_history_cve_id'),
        'cve_epss_history',
        ['cve_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_cve_epss_history_id'),
        'cve_epss_history',
        ['id'],
        unique=False,
    )


def downgrade() -> None:
    """Drop the EPSS history table."""
    op.drop_index(
        op.f('ix_cve_epss_history_id'),
        table_name='cve_epss_history',
    )
    op.drop_index(
        op.f('ix_cve_epss_history_cve_id'),
        table_name='cve_epss_history',
    )
    op.drop_table('cve_epss_history')
