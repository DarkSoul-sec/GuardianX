"""Tests for the activity log and login tracking."""

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.roles import UserRole
from app.database import models  # noqa: F401 - register mapped models
from app.database.base import Base
from app.models.user import User
from app.services.activity_service import (
    list_activities,
    recent_login_history,
    record_activity,
)


class ActivityLogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(cls.engine)
        cls.session_factory = sessionmaker(bind=cls.engine, expire_on_commit=False)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def setUp(self) -> None:
        self.db: Session = self.session_factory()
        self.user = User(
            username="socuser",
            email="soc@example.com",
            password_hash="unused",
            role=UserRole.USER,
            is_active=True,
        )
        self.db.add(self.user)
        self.db.flush()
        self.db.commit()
        self.user_id = self.user.id

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)

    def test_record_and_list_activity(self) -> None:
        record_activity(
            self.db,
            user_id=self.user_id,
            action="asset_created",
            entity_type="asset",
            entity_id=7,
            detail="Created asset Web-01",
        )
        self.db.commit()

        result = list_activities(self.db, self.user_id)

        self.assertEqual(result["total"], 1)
        entry = result["items"][0]
        self.assertEqual(entry.action, "asset_created")
        self.assertEqual(entry.entity_id, 7)
        self.assertEqual(entry.user_id, self.user_id)

    def test_activity_is_scoped_to_user(self) -> None:
        other = User(
            username="bob",
            email="bob@example.com",
            password_hash="unused",
            role=UserRole.USER,
            is_active=True,
        )
        self.db.add(other)
        self.db.commit()

        record_activity(
            self.db,
            user_id=other.id,
            action="login",
            detail="signed in",
        )
        self.db.commit()

        self.assertEqual(list_activities(self.db, self.user_id)["total"], 0)
        self.assertEqual(
            list_activities(self.db, other.id)["total"],
            1,
        )

    def test_recent_login_history(self) -> None:
        record_activity(
            self.db,
            user_id=self.user_id,
            action="login",
            detail="signed in",
            ip_address="127.0.0.1",
        )
        record_activity(
            self.db,
            user_id=self.user_id,
            action="logout",
            detail="signed out",
        )
        self.db.commit()

        logins = recent_login_history(self.db, self.user_id)

        self.assertEqual(len(logins), 1)
        self.assertEqual(logins[0].action, "login")
        self.assertEqual(logins[0].ip_address, "127.0.0.1")

    def test_activity_persists_before_commit(self) -> None:
        entry = record_activity(
            self.db,
            user_id=self.user_id,
            action="scan_completed",
            detail="Finished",
        )
        self.db.commit()

        reloaded = recent_login_history(self.db, self.user_id)
        self.assertFalse(reloaded)

        self.assertEqual(entry.action, "scan_completed")


if __name__ == "__main__":
    unittest.main()