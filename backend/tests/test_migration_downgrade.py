"""Regression: the scan_status enum migration must never write to pg_enum.

Migration ``9d4e6a1b2c3d`` adds the ``CANCELLED`` value to the ``scan_status``
enum type. PostgreSQL cannot remove a value from an enum type, so the
downgrade must refuse to run rather than mutate the ``pg_enum`` system catalog
(an unsupported operation that can corrupt enum-typed data and would never be
permitted for a least-privilege migration role). These tests guard that policy
so the unsafe catalog write cannot silently return.
"""

import importlib.util
import inspect
import pathlib
import unittest

_BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
_MIGRATION_PATH = (
    _BACKEND_DIR
    / "alembic"
    / "versions"
    / "9d4e6a1b2c3d_add_cancelled_scan_status.py"
)


def _load_migration():
    spec = importlib.util.spec_from_file_location(
        "migration_9d4e6a1b2c3d",
        _MIGRATION_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ScanStatusMigrationDowngradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_migration()
        cls.source = _MIGRATION_PATH.read_text(encoding="utf-8")

    def test_downgrade_raises_instead_of_mutating_catalog(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            self.module.downgrade()

        message = str(ctx.exception)
        self.assertIn("cannot be downgraded in place", message)

    def test_downgrade_error_documents_restore_recovery_path(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            self.module.downgrade()

        message = str(ctx.exception)
        self.assertIn("restore the database from a backup", message)

    def test_downgrade_performs_no_database_write(self) -> None:
        source = inspect.getsource(self.module.downgrade)
        self.assertNotIn("op.execute", source)
        self.assertNotIn("DELETE", source.upper())
        self.assertNotIn("DELETE FROM pg_enum", source.upper())

    def test_unsafe_catalog_write_is_absent_from_whole_migration(self) -> None:
        # Guards against the catalog DELETE returning anywhere in the file.
        self.assertNotIn("DELETE FROM pg_enum", self.source)

    def test_upgrade_still_adds_enum_value_via_alter_type(self) -> None:
        self.assertIn("ALTER TYPE", self.source)
        self.assertIn("ADD VALUE", self.source)


if __name__ == "__main__":
    unittest.main()
