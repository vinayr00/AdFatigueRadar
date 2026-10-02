"""Script to initialize or verify the primary administrator account."""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except ImportError:
    pass

from backend.db.repository import repository
from backend.db.security import hash_password


def create_initial_admin() -> int:
    email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
    password = os.environ.get("ADMIN_PASSWORD", "").strip()

    if not email or not password:
        print("[ERROR] Both ADMIN_EMAIL and ADMIN_PASSWORD environment variables are required.")
        return 1

    existing = repository.get_user_by_email(email)
    if existing:
        session = repository._session()
        if session:
            try:
                from backend.db.models import UserRow
                row = session.get(UserRow, existing.id)
                if row:
                    row.password_hash = hash_password(password)
                    row.role = "ADMIN"
                    row.is_active = True
                    row.updated_at = datetime.now(timezone.utc)
                    session.commit()
            finally:
                session.close()
        print(f"[INFO] Admin user '{email}' already exists. Password updated securely.")
        return 0

    user_id = f"user_{uuid4().hex[:12]}"
    pwd_hash = hash_password(password)
    now = datetime.now(timezone.utc)

    repository.create_user({
        "id": user_id,
        "email": email,
        "password_hash": pwd_hash,
        "full_name": "System Administrator",
        "role": "ADMIN",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    })

    print(f"[SUCCESS] Admin user '{email}' created successfully with role 'ADMIN'.")
    return 0


if __name__ == "__main__":
    sys.exit(create_initial_admin())
