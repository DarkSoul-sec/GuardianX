"""add user_agent and ip_address to refresh_tokens

Revision ID: 190ffd6b5419
Revises: b6c7d8e9f0a1
Create Date: 2026-08-08 01:41:05.156679

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '190ffd6b5419'
down_revision: Union[str, Sequence[str], None] = 'b6c7d8e9f0a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "refresh_tokens",
        sa.Column("user_agent", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "refresh_tokens",
        sa.Column("ip_address", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("refresh_tokens", "ip_address")
    op.drop_column("refresh_tokens", "user_agent")
