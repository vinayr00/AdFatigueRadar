"""
backend/tests/api/test_auth_routes.py
--------------------------------------
Integration tests for backend authentication routes (/api/auth/*)
against real PostgreSQL and Argon2 password verification.
"""
from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient

from backend.db.repository import repository
from backend.db.security import hash_password
from backend.main import app


@pytest.fixture
def auth_client():
    os.environ["ADFR_API_KEY"] = "test-api-key"
    os.environ["ADFR_HMAC_SECRET"] = "test-hmac-secret"
    return TestClient(app)


@pytest.fixture
def test_user():
    user_email = "authtest_user@example.com"
    # Ensure cleanup before
    existing = repository.get_user_by_email(user_email)
    if existing:
        repository.delete_user(existing.id)

    raw_password = "SecurePassword123!"
    user = repository.create_user({
        "id": "user_authtest_1",
        "email": user_email,
        "password_hash": hash_password(raw_password),
        "full_name": "Auth Test User",
        "role": "ADMIN",
        "is_active": True,
    })
    yield user, raw_password
    # Cleanup after
    repository.delete_user("user_authtest_1")


def test_login_success_and_cookie_issued(auth_client, test_user):
    user, raw_password = test_user
    response = auth_client.post(
        "/api/auth/login",
        json={"email": user.email, "password": raw_password},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == user.email
    assert data["user"]["role"] == "ADMIN"
    assert data["user"]["full_name"] == "Auth Test User"
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]

    # Cookie must be present
    assert "adfr_session" in response.cookies
    assert response.headers.get("set-cookie") is not None
    assert "HttpOnly" in response.headers.get("set-cookie")


def test_login_invalid_password(auth_client, test_user):
    user, _ = test_user
    response = auth_client.post(
        "/api/auth/login",
        json={"email": user.email, "password": "WrongPassword999!"},
    )
    assert response.status_code == 401
    assert "adfr_session" not in response.cookies


def test_login_unknown_user(auth_client):
    response = auth_client.post(
        "/api/auth/login",
        json={"email": "nonexistent_person_xyz@example.com", "password": "SomePassword123!"},
    )
    assert response.status_code == 401


def test_me_endpoint_with_valid_session(auth_client, test_user):
    user, raw_password = test_user
    # Login first
    login_res = auth_client.post(
        "/api/auth/login",
        json={"email": user.email, "password": raw_password},
    )
    assert login_res.status_code == 200

    # Call /api/auth/me with session cookie
    me_res = auth_client.get("/api/auth/me")
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["user"]["id"] == user.id
    assert me_data["user"]["email"] == user.email
    assert me_data["user"]["role"] == "ADMIN"
    assert "password_hash" not in me_data["user"]


def test_me_endpoint_unauthenticated(auth_client):
    # Fresh client with no cookie
    auth_client.cookies.clear()
    response = auth_client.get("/api/auth/me")
    assert response.status_code == 401


def test_logout_clears_cookie(auth_client, test_user):
    user, raw_password = test_user
    # Login
    auth_client.post(
        "/api/auth/login",
        json={"email": user.email, "password": raw_password},
    )
    assert auth_client.get("/api/auth/me").status_code == 200

    # Logout
    logout_res = auth_client.post("/api/auth/logout")
    assert logout_res.status_code == 200

    # /me should now fail
    assert auth_client.get("/api/auth/me").status_code == 401
