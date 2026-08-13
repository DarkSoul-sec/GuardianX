#!/usr/bin/env python3
"""Deployment-level password recovery for a GuardianX user (local edition).

Local-mode administrators have no email address, so the email-based
"forgot password" flow cannot recover their account. This script is the
intended recovery path: it must be run on the GuardianX host with access to
the backend's ``.env`` and the database, i.e. by whoever holds administrative
control of the installation.

Security properties
-------------------
* No unauthenticated web route can reset an administrator password.
* The new password is validated against the same policy (>= 12 characters)
  and hashed with the same scheme the API uses.
* All existing refresh tokens for the user are revoked, forcing re-login.
* The password is never printed, logged, or stored in plaintext.

Usage
-----
    cd backend
    .venv/bin/python scripts/reset_admin_password.py

"""
from __future__ import annotations

import getpass
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.security import get_password_hash  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.token_service import revoke_all_refresh_tokens  # noqa: E402

MIN_PASSWORD_LENGTH = 12


def main() -> int:
    username = input("Username of the account to recover: ").strip()

    if not username:
        print("A username is required.")
        return 1

    password = getpass.getpass("New password (hidden): ")
    confirm = getpass.getpass("Confirm new password (hidden): ")

    if password != confirm:
        print("Passwords do not match.")
        return 1

    if len(password) < MIN_PASSWORD_LENGTH:
        print(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters "
            "long."
        )
        return 1

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()

        if user is None:
            print(f"No user named '{username}' was found.")
            return 1

        user.password_hash = get_password_hash(password)
        db.commit()
        db.refresh(user)

        revoked = revoke_all_refresh_tokens(db, user.id)
        if revoked:
            print(f"Revoked {revoked} active session(s) for {username}.")
    finally:
        db.close()

    print(f"Password for '{username}' has been reset successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
