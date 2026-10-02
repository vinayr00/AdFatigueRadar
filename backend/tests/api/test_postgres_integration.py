"""Real Supabase PostgreSQL Database Integration Tests.

Validates:
1. PostgreSQL connectivity and version
2. Schema & table catalog verification
3. Full CRUD operations through repository
4. Transaction rollback vs commit
5. Foreign key constraint enforcement & cascade deletes
6. Persistence across fresh sessions
7. User / Admin creation and duplicate prevention
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError

from backend.db.models import (
    ActionRow,
    AdRow,
    AuditEventRow,
    CampaignRow,
    CommentRow,
    NLPResultRow,
    ReplaySessionRow,
    RiskSnapshotRow,
    TelemetryRow,
    ThresholdOverrideRow,
    UserRow,
    WorkspaceSettingsRow,
)
from backend.db.repository import repository
from backend.db.security import hash_password, verify_password
from backend.db.session import engine, SessionLocal, database_configured


@pytest.fixture(scope="module")
def check_db():
    if not database_configured() or engine is None:
        pytest.skip("Database not configured in environment")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        pytest.skip(f"Supabase PostgreSQL unreachable: {e}")


def test_01_real_postgres_connection(check_db):
    """Verify live PostgreSQL version and connection."""
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version()")).scalar()
        assert version is not None
        assert "PostgreSQL" in version


def test_02_all_application_tables_exist(check_db):
    """Verify all 13 application tables exist in PostgreSQL."""
    with engine.connect() as conn:
        inspector = inspect(conn)
        tables = set(inspector.get_table_names())

    expected_tables = {
        "campaigns",
        "ads",
        "comments",
        "nlp_results",
        "telemetry",
        "risk_snapshots",
        "actions",
        "audit_events",
        "threshold_overrides",
        "automation_rules",
        "workspace_settings",
        "replay_sessions",
        "users",
    }
    assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"


def test_03_campaign_crud_cycle(check_db):
    """Verify Create, Read, Update, Delete cycle for a campaign."""
    cid = f"test_camp_{uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)

    # 1. CREATE
    repository.save_campaign({
        "id": cid,
        "name": "Integration Test Campaign",
        "platform": "meta",
        "status": "ACTIVE",
        "pre_block_state": None,
        "budget": 5000.0,
        "created_at": now,
        "metadata_json": {"test": True},
    })

    # 2. READ
    state = repository.get_campaign_state(cid)
    assert state is not None
    assert state[0] == "ACTIVE"
    assert state[1] is None

    view = repository.get_campaign_view(cid)
    assert view is not None
    assert view["name"] == "Integration Test Campaign"
    assert view["platform"] == "meta"

    # 3. UPDATE
    repository.save_campaign_state(cid, "PAUSED", "ACTIVE")
    updated_state = repository.get_campaign_state(cid)
    assert updated_state == ("PAUSED", "ACTIVE")

    # 4. DELETE
    deleted = repository.delete_campaign(cid)
    assert deleted is True
    assert repository.get_campaign_state(cid) is None


def test_04_transaction_rollback_and_commit(check_db):
    """Verify transaction rollback does NOT persist, but commit does."""
    cid_rb = f"test_rb_{uuid4().hex[:8]}"
    cid_cm = f"test_cm_{uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)

    # Test Rollback
    session = SessionLocal()
    try:
        session.add(CampaignRow(
            id=cid_rb,
            name="Rollback Campaign",
            platform="meta",
            status="ACTIVE",
            created_at=now,
            metadata_json={},
        ))
        session.rollback()
    finally:
        session.close()

    # Verify not persisted
    session2 = SessionLocal()
    try:
        assert session2.get(CampaignRow, cid_rb) is None
    finally:
        session2.close()

    # Test Commit
    session3 = SessionLocal()
    try:
        session3.add(CampaignRow(
            id=cid_cm,
            name="Commit Campaign",
            platform="meta",
            status="ACTIVE",
            created_at=now,
            metadata_json={},
        ))
        session3.commit()
    finally:
        session3.close()

    # Verify persisted and clean up
    session4 = SessionLocal()
    try:
        row = session4.get(CampaignRow, cid_cm)
        assert row is not None
        assert row.name == "Commit Campaign"
        session4.delete(row)
        session4.commit()
    finally:
        session4.close()


def test_05_foreign_key_and_cascade_delete(check_db):
    """Verify foreign key enforcement and cascade delete."""
    invalid_cid = f"nonexistent_{uuid4().hex[:8]}"
    comment_id = f"c_{uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)

    # 1. Invalid FK must be rejected
    session = SessionLocal()
    try:
        session.add(CommentRow(
            comment_id=comment_id,
            campaign_id=invalid_cid,
            ad_id="ad_1",
            timestamp=now,
            text="Invalid comment test",
            author_id_hmac="hmac_test_123",
        ))
        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.rollback()
        session.close()

    # 2. Valid FK cascade delete
    valid_cid = f"test_casc_{uuid4().hex[:8]}"
    valid_comment = f"c_{uuid4().hex[:8]}"
    session2 = SessionLocal()
    try:
        session2.add(CampaignRow(
            id=valid_cid,
            name="Cascade Test",
            platform="meta",
            status="ACTIVE",
            created_at=now,
            metadata_json={},
        ))
        session2.add(CommentRow(
            comment_id=valid_comment,
            campaign_id=valid_cid,
            ad_id="ad_1",
            timestamp=now,
            text="Valid comment",
            author_id_hmac="hmac_valid",
        ))
        session2.commit()
    finally:
        session2.close()

    # Delete parent campaign -> comment must be cascade deleted
    repository.delete_campaign(valid_cid)

    session3 = SessionLocal()
    try:
        assert session3.get(CampaignRow, valid_cid) is None
        assert session3.get(CommentRow, valid_comment) is None
    finally:
        session3.close()


def test_06_persistence_across_fresh_sessions(check_db):
    """Verify that records are persisted to PostgreSQL disk/Supabase, not in-memory."""
    cid = f"test_fresh_{uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)

    # Write in Session 1
    session1 = SessionLocal()
    try:
        session1.add(CampaignRow(
            id=cid,
            name="Fresh Session Test",
            platform="google",
            status="ACTIVE",
            created_at=now,
            metadata_json={"fresh": True},
        ))
        session1.commit()
    finally:
        session1.close()

    # Read from brand new Session 2
    session2 = SessionLocal()
    try:
        retrieved = session2.get(CampaignRow, cid)
        assert retrieved is not None
        assert retrieved.name == "Fresh Session Test"
        assert retrieved.platform == "google"
        assert retrieved.metadata_json == {"fresh": True}
        # Cleanup
        session2.delete(retrieved)
        session2.commit()
    finally:
        session2.close()


def test_07_user_foundation_and_admin_creation(check_db):
    """Verify User model, password hashing with Argon2, and admin creation."""
    test_email = f"test_admin_{uuid4().hex[:6]}@example.com"
    raw_password = "SecurePassword2026!"
    pwd_hash = hash_password(raw_password)
    now = datetime.now(timezone.utc)

    # 1. Create User
    user = repository.create_user({
        "id": f"usr_{uuid4().hex[:8]}",
        "email": test_email,
        "password_hash": pwd_hash,
        "full_name": "Test Admin",
        "role": "ADMIN",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    })
    assert user is not None
    assert user.email == test_email
    assert user.role == "ADMIN"
    assert verify_password(user.password_hash, raw_password) is True
    assert verify_password(user.password_hash, "WrongPassword") is False

    # 2. Duplicate email constraint must be enforced
    with pytest.raises(IntegrityError):
        repository.create_user({
            "id": f"usr_{uuid4().hex[:8]}",
            "email": test_email,  # duplicate
            "password_hash": pwd_hash,
            "full_name": "Duplicate Admin",
            "role": "ADMIN",
            "is_active": True,
            "created_at": now,
        })

    # 3. Read back
    retrieved = repository.get_user_by_email(test_email)
    assert retrieved is not None
    assert retrieved.role == "ADMIN"

    # 4. Clean up
    deleted = repository.delete_user(user.id)
    assert deleted is True
    assert repository.get_user_by_email(test_email) is None
