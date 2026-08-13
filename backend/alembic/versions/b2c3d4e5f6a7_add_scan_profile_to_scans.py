"""add scan_profile to scans

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f7
Create Date: 2026-08-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Track the port-coverage profile chosen for each scan."""
    op.add_column(
        'scans',
        sa.Column(
            'scan_profile',
            sa.String(length=20),
            server_default='standard',
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Drop the scan profile column."""
    op.drop_column('scans', 'scan_profile')
