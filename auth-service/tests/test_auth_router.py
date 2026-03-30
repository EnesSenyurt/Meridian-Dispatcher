from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from pymongo.errors import DuplicateKeyError

from app.auth_utils import SECRET_KEY, ALGORITHM, hash_password
from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# /auth/register
# ---------------------------------------------------------------------------

def test_register_returns_201(monkeypatch):
    inserted_id = MagicMock()
    inserted_id.__str__ = lambda self: "64f0000000000000000000ab"

    async def fake_execute(collection, operation, *args, **kwargs):
        if operation == "find_one":
            return None
        if operation == "insert_one":
            result = MagicMock()
            result.inserted_id = inserted_id
            return result
        if operation == "create_index":
            return None

    with patch("app.router.db.execute", side_effect=fake_execute):
        resp = client.post(
            "/auth/register",
            json={"email": "new@example.com", "password": "secret", "role": "sender"},
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert data["role"] == "sender"
    assert "user_id" in data


def test_register_duplicate_via_find_one_returns_409(monkeypatch):
    async def fake_execute(collection, operation, *args, **kwargs):
        if operation == "find_one":
            return {"email": "existing@example.com"}
        if operation == "create_index":
            return None

    with patch("app.router.db.execute", side_effect=fake_execute):
        resp = client.post(
            "/auth/register",
            json={"email": "existing@example.com", "password": "x", "role": "courier"},
        )
    assert resp.status_code == 409


def test_register_duplicate_via_duplicate_key_error_returns_409():
    async def fake_execute(collection, operation, *args, **kwargs):
        if operation == "find_one":
            return None
        if operation == "insert_one":
            raise DuplicateKeyError("duplicate key")
        if operation == "create_index":
            return None

    with patch("app.router.db.execute", side_effect=fake_execute):
        resp = client.post(
            "/auth/register",
            json={"email": "race@example.com", "password": "x", "role": "sender"},
        )
    assert resp.status_code == 409


def test_register_invalid_email_returns_422():
    resp = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "x", "role": "sender"},
    )
    assert resp.status_code == 422


def test_register_invalid_role_returns_422():
    resp = client.post(
        "/auth/register",
        json={"email": "a@b.com", "password": "x", "role": "admin"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# /auth/login
# ---------------------------------------------------------------------------

def _make_user(email: str, password: str, role: str) -> dict:
    return {
        "_id": MagicMock(__str__=lambda self: "64f0000000000000000000ab"),
        "email": email,
        "password_hash": hash_password(password),
        "role": role,
    }


def test_login_returns_200_with_token():
    user = _make_user("u@example.com", "pass123", "courier")

    async def fake_execute(collection, operation, *args, **kwargs):
        if operation == "find_one":
            return user
        if operation == "create_index":
            return None

    with patch("app.router.db.execute", side_effect=fake_execute):
        resp = client.post(
            "/auth/login",
            json={"email": "u@example.com", "password": "pass123"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    payload = jwt.decode(data["access_token"], SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["email"] == "u@example.com"
    assert payload["role"] == "courier"


def test_login_wrong_password_returns_401():
    user = _make_user("u@example.com", "correctpass", "sender")

    async def fake_execute(collection, operation, *args, **kwargs):
        if operation == "find_one":
            return user
        if operation == "create_index":
            return None

    with patch("app.router.db.execute", side_effect=fake_execute):
        resp = client.post(
            "/auth/login",
            json={"email": "u@example.com", "password": "wrongpass"},
        )
    assert resp.status_code == 401


def test_login_unknown_email_returns_401():
    async def fake_execute(collection, operation, *args, **kwargs):
        if operation == "find_one":
            return None
        if operation == "create_index":
            return None

    with patch("app.router.db.execute", side_effect=fake_execute):
        resp = client.post(
            "/auth/login",
            json={"email": "nobody@example.com", "password": "x"},
        )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /auth/verify
# ---------------------------------------------------------------------------

def _make_token(sub: str = "uid1", email: str = "v@example.com", role: str = "sender") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "email": email,
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=24),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def test_verify_valid_token_returns_user_info():
    token = _make_token()
    resp = client.get("/auth/verify", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "v@example.com"
    assert data["role"] == "sender"
    assert data["user_id"] == "uid1"


def test_verify_missing_authorization_header_returns_422():
    resp = client.get("/auth/verify")
    # FastAPI returns 422 when a required Header is missing
    assert resp.status_code == 422


def test_verify_missing_bearer_prefix_returns_401():
    token = _make_token()
    resp = client.get("/auth/verify", headers={"Authorization": token})
    assert resp.status_code == 401


def test_verify_invalid_token_returns_401():
    resp = client.get("/auth/verify", headers={"Authorization": "Bearer not.a.real.token"})
    assert resp.status_code == 401


def test_verify_expired_token_returns_401():
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "x",
        "email": "x@x.com",
        "role": "sender",
        "iat": now - timedelta(hours=48),
        "exp": now - timedelta(hours=24),
    }
    expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    resp = client.get("/auth/verify", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401
