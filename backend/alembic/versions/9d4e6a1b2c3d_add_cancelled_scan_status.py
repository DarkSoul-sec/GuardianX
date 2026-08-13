"""add_cancelled_scan_status

Revision ID: 9d4e6a1b2c3d
Revises: 06edc0c5c40c
Create Date: 2026-08-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "9d4e6a1b2c3d"
down_revision: Union[str, Sequence[str], None] = "06edc0c5c40c"
branch_labels = None
depends_on = None

_ENUM_NAME = "scan_status"
_NEW_LABEL = "CANCELLED"


def _enum_label_exists(bind, label: str) -> bool:
    row = bind.execute(
        sa.text(
            """
            SELECT 1
            FROM pg_enum e
            JOIN pg_type t ON e.enumtypid = t.oid
            WHERE t.typname = :enum_name
              AND e.enumlabel = :label
            """
        ).bindparams(
            enum_name=_ENUM_NAME,
            label=label,
        )
    ).first()

    return row is not None


def upgrade() -> None:
    bind = op.get_bind()

    if _enum_label_exists(bind, _NEW_LABEL):
        return

    op.execute(
        sa.text(
            f"ALTER TYPE {_ENUM_NAME} ADD VALUE '{_NEW_LABEL}'"
        )
    )


class CannotDowngradeError(RuntimeError):
    """Raised when a migration cannot be rolled back safely in place."""


def downgrade() -> None:
    # PostgreSQL cannot remove a value from an enum type (ALTER TYPE ... DROP
    # VALUE does not exist), and deleting rows from the pg_enum system catalog
    # is unsupported: it can corrupt enum-typed columns and is not an operation
    # a least-privilege migration role should ever perform. GuardianX therefore
    # refuses to downgrade this migration in place.
    #
    # Supported recovery path:
    #   1. Stop the stack: `docker compose down` (keeps the database volume).
    #   2. Restore the `postgres_data` volume from a backup taken before this
    #      migration ran, or dump/restore the affected tables with the old enum
    #      definition.
    #   3. Bring the stack back up: `docker compose up -d --build`.
    #
    # See docs/DEPLOYMENT.md -> "PostgreSQL enum limitation (downgrades)".
    #
    # This function performs no database access at all, so it never requires
    # SUPERUSER and never touches the system catalog.
    raise CannotDowngradeError(
        "Migration 9d4e6a1b2c3d (add_cancelled_scan_status) cannot be "
        "downgraded in place: PostgreSQL does not support removing a value "
        "from the 'scan_status' enum type, and writing to the pg_enum system "
        "catalog is unsupported and can corrupt existing data. To revert, "
        "restore the database from a backup taken before this migration ran "
        "(see docs/DEPLOYMENT.md -> 'PostgreSQL enum limitation "
        "(downgrades)')."
    )
