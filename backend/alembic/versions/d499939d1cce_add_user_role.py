"""add_user_role

Revision ID: d499939d1cce
Revises: 5cba0f44d560
Create Date: 2026-07-15

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d499939d1cce"
down_revision: Union[str, Sequence[str], None] = "5cba0f44d560"
branch_labels = None
depends_on = None


user_role = sa.Enum(
    "ADMIN",
    "SECURITY_ENGINEER",
    "ANALYST",
    "VIEWER",
    "USER",
    name="user_role",
)


def upgrade() -> None:
    bind = op.get_bind()

    # Create PostgreSQL ENUM type
    user_role.create(bind, checkfirst=True)

    # Add the column with a temporary default for existing rows
    op.add_column(
        "users",
        sa.Column(
            "role",
            user_role,
            nullable=False,
            server_default="USER",
        ),
    )

    # Remove the default so future inserts use the application default
    op.alter_column(
        "users",
        "role",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column("users", "role")

    bind = op.get_bind()
    user_role.drop(bind, checkfirst=True)
