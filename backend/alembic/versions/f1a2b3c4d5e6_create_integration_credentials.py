"""create integration_credentials table

Revision ID: f1a2b3c4d5e6
Revises: b7f3c8a2d1e4
Create Date: 2026-08-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'b7f3c8a2d1e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the per-user integration credential store."""
    op.create_table(
        'integration_credentials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('encrypted_api_key', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('last_tested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
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
        sa.UniqueConstraint(
            'user_id',
            'provider',
            name='uq_integration_credentials_user_provider',
        ),
    )
    op.create_index(
        op.f('ix_integration_credentials_user_id'),
        'integration_credentials',
        ['user_id'],
        unique=False,
    )


def downgrade() -> None:
    """Drop the integration credential store."""
    op.drop_index(
        op.f('ix_integration_credentials_user_id'),
        table_name='integration_credentials',
    )
    op.drop_table('integration_credentials')
