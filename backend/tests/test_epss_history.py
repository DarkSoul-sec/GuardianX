"""Tests for persistent EPSS history capture."""

import unittest
from datetime import date, timedelta
from unittest import mock

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import models  # noqa: F401 - register mapped models
from app.database.base import Base
from app.integrations.threat_intel import epss_history
from app.integrations.threat_intel.epss_history import get_history, record_snapshot
from app.models.cve_epss_history import CveEpssHistory

_TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TEST_SESSION = sessionmaker(
    bind=_TEST_ENGINE,
    class_=Session,
    expire_on_commit=False,
)


class EpssHistoryServiceTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(_TEST_ENGINE)

    def setUp(self):
        with _TEST_SESSION() as db:
            db.query(CveEpssHistory).delete()
            db.commit()

    def _patch_session(self):
        return mock.patch.object(
            epss_history,
            "SessionLocal",
            _TEST_SESSION,
        )

    def test_record_and_read_snapshot(self):
        with self._patch_session():
            record_snapshot("CVE-2024-0001", 0.85, 0.99)
            history = get_history("CVE-2024-0001")

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["score"], 0.85)
        self.assertEqual(history[0]["percentile"], 0.99)
        self.assertEqual(history[0]["date"], date.today().isoformat())

    def test_snapshot_upserts_same_day(self):
        with self._patch_session():
            record_snapshot("CVE-2024-0001", 0.40, 0.80)
            record_snapshot("CVE-2024-0001", 0.95, 0.99)
            history = get_history("CVE-2024-0001")

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["score"], 0.95)

    def test_history_is_scoped_to_cve(self):
        with self._patch_session():
            record_snapshot("CVE-2024-0001", 0.90, 0.99)
            record_snapshot("CVE-2024-0002", 0.10, 0.40)

            one = get_history("CVE-2024-0001")
            two = get_history("CVE-2024-0002")
            none = get_history("CVE-2024-9999")

        self.assertEqual(len(one), 1)
        self.assertEqual(len(two), 1)
        self.assertEqual(none, [])

    def test_history_orders_newest_first(self):
        with _TEST_SESSION() as db:
            db.add_all(
                [
                    CveEpssHistory(
                        cve_id="CVE-2024-0001",
                        score=0.10,
                        percentile=0.20,
                        recorded_on=date.today() - timedelta(days=2),
                    ),
                    CveEpssHistory(
                        cve_id="CVE-2024-0001",
                        score=0.50,
                        percentile=0.70,
                        recorded_on=date.today() - timedelta(days=1),
                    ),
                ]
            )
            db.commit()

        with self._patch_session():
            history = get_history("CVE-2024-0001")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["score"], 0.50)
        self.assertEqual(history[1]["score"], 0.10)

    def test_get_history_tolerates_db_failure(self):
        with mock.patch.object(
            epss_history,
            "SessionLocal",
            _TEST_SESSION,
        ):
            with mock.patch.object(
                _TEST_SESSION,
                "__call__",
                side_effect=RuntimeError("boom"),
            ):
                self.assertEqual(get_history("CVE-2024-0001"), [])


if __name__ == "__main__":
    unittest.main()
