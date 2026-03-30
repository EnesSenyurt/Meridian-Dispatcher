import httpx
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

_SECRET = "test-secret-key-for-testing-only"
_ALGORITHM = "HS256"


def _make_token(exp_delta: timedelta = timedelta(hours=24)) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "user-id",
        "email": "test@example.com",
        "role": "sender",
        "iat": now,
        "exp": now + exp_delta,
    }
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def _fake_upstream(status_code: int = 200, content: bytes = b"{}"):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.content = content
    resp.headers = httpx.Headers({"content-type": "application/json"})
    return resp


# ---------------------------------------------------------------------------
# Public paths bypass auth
# ---------------------------------------------------------------------------

class TestPublicPaths:

    def test_auth_register_bypasses_auth(self):
        from app.main import app
        with patch("app.main.forward_request", new_callable=AsyncMock) as mock_fwd:
            mock_fwd.return_value = _fake_upstream(201)
            with TestClient(app, raise_server_exceptions=False) as client:
                resp = client.post("/auth/register", json={})
        # Middleware did not block — reached the proxy (or got 422 from upstream mock)
        assert resp.status_code != 401

    def test_auth_login_bypasses_auth(self):
        from app.main import app
        with patch("app.main.forward_request", new_callable=AsyncMock) as mock_fwd:
            mock_fwd.return_value = _fake_upstream(200)
            with TestClient(app, raise_server_exceptions=False) as client:
                resp = client.post("/auth/login", json={})
        assert resp.status_code != 401

    def test_health_bypasses_auth(self):
        from app.main import app
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/health")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Protected paths — no / bad token → 401
# ---------------------------------------------------------------------------

class TestProtectedPathsUnauthorized:

    def test_no_token_returns_401(self):
        from app.main import app
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/delivery/orders")
        assert resp.status_code == 401

    def test_no_token_has_www_authenticate_header(self):
        from app.main import app
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/delivery/orders")
        assert resp.headers.get("www-authenticate") == "Bearer"

    def test_malformed_token_returns_401(self):
        from app.main import app
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get(
                "/delivery/orders",
                headers={"authorization": "NotBearer something"},
            )
        assert resp.status_code == 401

    def test_invalid_jwt_returns_401(self):
        from app.main import app
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get(
                "/delivery/orders",
                headers={"authorization": "Bearer not.a.real.jwt"},
            )
        assert resp.status_code == 401
        assert resp.headers.get("www-authenticate") == "Bearer"

    def test_expired_token_returns_401(self):
        from app.main import app
        expired_token = _make_token(exp_delta=timedelta(hours=-1))
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get(
                "/delivery/orders",
                headers={"authorization": f"Bearer {expired_token}"},
            )
        assert resp.status_code == 401
        assert resp.headers.get("www-authenticate") == "Bearer"

    def test_wrong_secret_token_returns_401(self):
        from app.main import app
        now = datetime.now(timezone.utc)
        token = jwt.encode(
            {"sub": "x", "exp": now + timedelta(hours=1)},
            "wrong-secret",
            algorithm=_ALGORITHM,
        )
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get(
                "/delivery/orders",
                headers={"authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Protected paths — valid token → passes through to upstream
# ---------------------------------------------------------------------------

class TestProtectedPathsAuthorized:

    def test_valid_token_reaches_upstream(self):
        from app.main import app
        token = _make_token()

        with patch("app.main.forward_request", new_callable=AsyncMock) as mock_fwd:
            mock_fwd.return_value = _fake_upstream(200, b'{"orders":[]}')
            with TestClient(app, raise_server_exceptions=False) as client:
                resp = client.get(
                    "/delivery/orders",
                    headers={"authorization": f"Bearer {token}"},
                )

        assert resp.status_code == 200
        mock_fwd.assert_awaited_once()

    def test_valid_token_tracking_path(self):
        from app.main import app
        token = _make_token()

        with patch("app.main.forward_request", new_callable=AsyncMock) as mock_fwd:
            mock_fwd.return_value = _fake_upstream(200, b'{"status":"in_transit"}')
            with TestClient(app, raise_server_exceptions=False) as client:
                resp = client.get(
                    "/tracking/shipments/99",
                    headers={"authorization": f"Bearer {token}"},
                )

        assert resp.status_code == 200
        call_kwargs = mock_fwd.call_args.kwargs
        assert "/tracking/shipments/99" in call_kwargs["url"]
