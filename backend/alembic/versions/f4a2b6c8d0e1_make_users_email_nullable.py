"""make users.email nullable for local administrators

Revision ID: f4a2b6c8d0e1
Revises: 190ffd6b5419
Create Date: 2026-08-11

Local-mode administrators are created without an email address, so the
``users.email`` column must accept NULL. Postgres keeps the unique index
working for non-NULL values (multiple NULLs remain allowed), so no index
change is required.

Revision ID: f4a2b6c8d0e1
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f4a2b6c8d0e1"
down_revision: Union[str, Sequence[str], None] = "190ffd6b5419"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "users",
        "email",
        existing_type=sa.String(length=255),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Existing local administrators have a NULL email; backfill them to a
    # placeholder is unsafe, so this downgrade fails loudly if any NULL rows
    # exist rather than silently corrupting data.
    bind = op.get_bind()
    null_emails = bind.execute(
        sa.text("SELECT COUNT(*) FROM users WHERE email IS NULL")
    ).scalar()

    if null_emails:
        raise RuntimeError(
            "Cannot downgrade: users with a NULL email exist. Assign an "
            "email to those users before downgrading."
        )

    op.alter_column(
        "users",
        "email",
        existing_type=sa.String(length=255),
        nullable=False,
    )
