"""create_assets_table

Revision ID: 8c7e7a469e0f
Revises: d499939d1cce
Create Date: 2026-07-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision: str = "8c7e7a469e0f"
down_revision: Union[str, Sequence[str], None] = "d499939d1cce"
branch_labels = None
depends_on = None


asset_type_enum = postgresql.ENUM(
    "SERVER",
    "WORKSTATION",
    "WEBSITE",
    "DOMAIN",
    "IP_ADDRESS",
    "API",
    "CLOUD",
    "MOBILE",
    "OTHER",
    name="asset_type",
    create_type=False,
)


def upgrade() -> None:
    asset_type_enum.create(
        op.get_bind(),
        checkfirst=True,
    )

    op.create_table(
        "assets",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),

        sa.Column(
            "name",
            sa.String(150),
            nullable=False,
        ),

        sa.Column(
            "asset_type",
            asset_type_enum,
            nullable=False,
        ),

        sa.Column(
            "ip_address",
            sa.String(45),
            nullable=True,
        ),

        sa.Column(
            "domain",
            sa.String(255),
            nullable=True,
        ),

        sa.Column(
            "operating_system",
            sa.String(100),
            nullable=True,
        ),

        sa.Column(
            "environment",
            sa.String(50),
            nullable=True,
        ),

        sa.Column(
            "owner",
            sa.String(100),
            nullable=True,
        ),

        sa.Column(
            "criticality",
            sa.String(20),
            nullable=True,
        ),

        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_assets_id",
        "assets",
        ["id"],
    )

    op.create_index(
        "ix_assets_name",
        "assets",
        ["name"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_assets_name",
        table_name="assets",
    )

    op.drop_index(
        "ix_assets_id",
        table_name="assets",
    )

    op.drop_table("assets")

    asset_type_enum.drop(
        op.get_bind(),
        checkfirst=True,
    )
