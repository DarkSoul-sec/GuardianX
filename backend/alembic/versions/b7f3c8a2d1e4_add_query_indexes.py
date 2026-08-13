"""add query performance indexes

Revision ID: b7f3c8a2d1e4
Revises: a7b8c9d0e1f2
Create Date: 2026-08-06 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b7f3c8a2d1e4'
down_revision: Union[str, Sequence[str], None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        'ix_findings_scan_result_id',
        'findings',
        ['scan_result_id'],
    )
    op.create_index(
        'ix_findings_cve',
        'findings',
        ['cve'],
    )
    op.create_index(
        'ix_findings_severity',
        'findings',
        ['severity'],
    )
    op.create_index(
        'ix_findings_status',
        'findings',
        ['status'],
    )
    op.create_index(
        'ix_findings_created_at',
        'findings',
        ['created_at'],
    )
    op.create_index(
        'ix_assets_created_by',
        'assets',
        ['created_by'],
    )
    op.create_index(
        'ix_assets_created_at',
        'assets',
        ['created_at'],
    )
    op.create_index(
        'ix_scans_status',
        'scans',
        ['status'],
    )
    op.create_index(
        'ix_scans_created_at',
        'scans',
        ['created_at'],
    )
    op.create_index(
        'ix_scheduled_scans_enabled_next_run',
        'scheduled_scans',
        ['enabled', 'next_run_at'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    for index in [
        'ix_scheduled_scans_enabled_next_run',
        'ix_scans_created_at',
        'ix_scans_status',
        'ix_assets_created_at',
        'ix_assets_created_by',
        'ix_findings_created_at',
        'ix_findings_status',
        'ix_findings_severity',
        'ix_findings_cve',
        'ix_findings_scan_result_id',
    ]:
        op.drop_index(index)
