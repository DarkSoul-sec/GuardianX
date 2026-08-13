"""create intelligence_searches table

Revision ID: a1b2c3d4e5f7
Revises: f1a2b3c4d5e6
Create Date: 2026-08-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the per-user threat intelligence search history."""
    op.create_table(
        'intelligence_searches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('resource_type', sa.String(length=10), nullable=False),
        sa.Column('resource', sa.String(length=2048), nullable=False),
        sa.Column('threat_level', sa.String(length=10), nullable=False),
        sa.Column('risk_score', sa.Integer(), nullable=False),
        sa.Column('reputation', sa.Integer(), nullable=False),
        sa.Column('detected', sa.Boolean(), nullable=False),
        sa.Column('malicious', sa.Integer(), nullable=False),
        sa.Column('suspicious', sa.Integer(), nullable=False),
        sa.Column('harmless', sa.Integer(), nullable=False),
        sa.Column('undetected', sa.Integer(), nullable=False),
        sa.Column('detection_ratio', sa.String(length=20), nullable=False),
        sa.Column('threat_category', sa.String(length=255), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_intelligence_searches_id'),
        'intelligence_searches',
        ['id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_intelligence_searches_user_created'),
        'intelligence_searches',
        ['user_id', 'created_at'],
        unique=False,
    )
    op.create_index(
        op.f('ix_intelligence_searches_user_type'),
        'intelligence_searches',
        ['user_id', 'resource_type'],
        unique=False,
    )


def downgrade() -> None:
    """Drop the threat intelligence search history."""
    op.drop_index(
        op.f('ix_intelligence_searches_user_type'),
        table_name='intelligence_searches',
    )
    op.drop_index(
        op.f('ix_intelligence_searches_user_created'),
        table_name='intelligence_searches',
    )
    op.drop_index(
        op.f('ix_intelligence_searches_id'),
        table_name='intelligence_searches',
    )
    op.drop_table('intelligence_searches')
