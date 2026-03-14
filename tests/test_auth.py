"""
Tests for authentication endpoints.

These tests exercise registration, login, and profile retrieval
without any real database or Redis dependency (SQLite in-memory + SimpleCache).
"""
import json
import pytest


# ── Helpers ──────────────────────────────────────────────────────────────────

def _register(client, name="Alice", email="alice@example.com", password="password123"):
    return client.post(
        "/api/auth/register",
        data=json.dumps({"name": name, "email": email, "password": password}),
        content_type="application/json",
    )


def _login(client, email="alice@example.com", password="password123"):
    return client.post(
        "/api/auth/login",
        data=json.dumps({"email": email, "password": password}),
        content_type="application/json",
    )


# ── Registration ──────────────────────────────────────────────────────────────

def test_register_success(client):
    """Valid registration returns 201 with user data."""
    resp = _register(client)
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["success"] is True
    assert "user" in body["data"]


def test_register_missing_fields(client):
    """Registration without required fields returns 422."""
    resp = client.post(
        "/api/auth/register",
        data=json.dumps({"email": "missing@example.com"}),
        content_type="application/json",
    )
    assert resp.status_code == 422
    body = resp.get_json()
    assert body["success"] is False


def test_register_duplicate_email(client):
    """Registering the same email twice returns an error."""
    _register(client, email="dup@example.com")
    resp = _register(client, email="dup@example.com")
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["success"] is False
    assert "already exists" in body["message"].lower()


# ── Login ─────────────────────────────────────────────────────────────────────

def test_login_success(client):
    """Registered user can log in and receives access_token."""
    _register(client, email="bob@example.com")
    resp = _login(client, email="bob@example.com")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert "access_token" in body["data"]
    assert "refresh_token" in body["data"]


def test_login_wrong_password(client):
    """Login with wrong password returns 401."""
    _register(client, email="carol@example.com")
    resp = _login(client, email="carol@example.com", password="wrongpassword")
    assert resp.status_code == 401
    body = resp.get_json()
    assert body["success"] is False


def test_login_nonexistent_user(client):
    """Login for non-existent user returns 401."""
    resp = _login(client, email="ghost@example.com")
    assert resp.status_code == 401
    body = resp.get_json()
    assert body["success"] is False


# ── Protected Endpoints ───────────────────────────────────────────────────────

def test_me_requires_auth(client):
    """GET /api/auth/me without token returns 401."""
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_with_valid_token(client):
    """GET /api/auth/me with a valid JWT returns the current user's profile."""
    _register(client, email="dave@example.com")
    login_resp = _login(client, email="dave@example.com")
    token = login_resp.get_json()["data"]["access_token"]

    resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["data"]["email"] == "dave@example.com"


# ── Ping ──────────────────────────────────────────────────────────────────────

def test_ping(client):
    """GET /api/auth/ping returns 200 without authentication."""
    resp = client.get("/api/auth/ping")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
