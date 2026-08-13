"""create_scans_tables

Revision ID: 475262f5e297
Revises: 8c7e7a469e0f
Create Date: 2026-07-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision: str = "475262f5e297"
down_revision: Union[str, Sequence[str], None] = "8c7e7a469e0f"
branch_labels = None
depends_on = None


scan_status_enum = postgresql.ENUM(
    "PENDING",
    "RUNNING",
    "COMPLETED",
    "FAILED",
    name="scan_status",
    create_type=False,
)


def upgrade() -> None:
    scan_status_enum.create(
        op.get_bind(),
        checkfirst=True,
    )

    op.create_table(
        "scans",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),

        sa.Column(
            "asset_id",
            sa.Integer(),
            sa.ForeignKey(
                "assets.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),

        sa.Column(
            "status",
            scan_status_enum,
            nullable=False,
        ),

        sa.Column(
            "scanner",
            sa.String(50),
            nullable=False,
        ),

        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "finished_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_scans_id",
        "scans",
        ["id"],
    )

    op.create_index(
        "ix_scans_asset_id",
        "scans",
        ["asset_id"],
    )

    op.create_table(
        "scan_results",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),

        sa.Column(
            "scan_id",
            sa.Integer(),
            sa.ForeignKey(
                "scans.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),

        sa.Column(
            "port",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "protocol",
            sa.String(10),
            nullable=False,
        ),

        sa.Column(
            "state",
            sa.String(20),
            nullable=False,
        ),

        sa.Column(
            "service",
            sa.String(100),
            nullable=True,
        ),

        sa.Column(
            "version",
            sa.String(255),
            nullable=True,
        ),

        sa.Column(
            "product",
            sa.String(255),
            nullable=True,
        ),

        sa.Column(
            "is_ssl",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.create_index(
        "ix_scan_results_id",
        "scan_results",
        ["id"],
    )

    op.create_index(
        "ix_scan_results_scan_id",
        "scan_results",
        ["scan_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_scan_results_scan_id",
        table_name="scan_results",
    )

    op.drop_index(
        "ix_scan_results_id",
        table_name="scan_results",
    )

    op.drop_table("scan_results")

    op.drop_index(
        "ix_scans_asset_id",
        table_name="scans",
    )

    op.drop_index(
        "ix_scans_id",
        table_name="scans",
    )

    op.drop_table("scans")

    scan_status_enum.drop(
        op.get_bind(),
        checkfirst=True,
    )
