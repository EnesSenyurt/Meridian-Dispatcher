import pytest
import httpx
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from jose import jwt

_SECRET = "test-secret-key-for-testing-only"
_ALGORITHM = "HS256"


def _make_valid_token() -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "test-user-id",
        "email": "test@example.com",
        "role": "sender",
        "iat": now,
        "exp": now + timedelta(hours=24),
    }
    return jwt.encode(payload, _SECRET, algorithm=_ALGORITHM)


def _auth_headers() -> dict:
    return {"authorization": f"Bearer {_make_valid_token()}"}


def _fake_httpx_response(status_code: int, content: bytes, headers: dict = None):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.content = content
    resp.headers = httpx.Headers(headers or {"content-type": "application/json"})
    return resp


class TestProxyRouterHappyPath:

    def test_auth_path_is_routed_and_200_returned(self):
        from app.main import app
        upstream_resp = _fake_httpx_response(200, b'{"token":"abc"}')

        with patch("app.main.forward_request", new_callable=AsyncMock) as mock_fwd:
            mock_fwd.return_value = upstream_resp
            with TestClient(app, raise_server_exceptions=False) as client:
                # /auth/login is a public path — no token needed
                response = client.get("/auth/login")

        assert response.status_code == 200
        call_kwargs = mock_fwd.call_args.kwargs
        assert "/auth/login" in call_kwargs["url"]

    def test_delivery_path_is_routed_and_201_returned(self):
        from app.main import app
        upstream_resp = _fake_httpx_response(201, b'{"id":99}')

        with patch("app.main.forward_request", new_callable=AsyncMock) as mock_fwd:
            mock_fwd.return_value = upstream_resp
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post(
                    "/delivery/orders",
                    json={"item": "box"},
                    headers=_auth_headers(),
                )

        assert response.status_code == 201

    def test_tracking_path_is_routed(self):
        from app.main import app
        upstream_resp = _fake_httpx_response(200, b'{}')

        with patch("app.main.forward_request", new_callable=AsyncMock) as mock_fwd:
            mock_fwd.return_value = upstream_resp
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.get("/tracking/shipments/42", headers=_auth_headers())

        assert response.status_code == 200
        call_kwargs = mock_fwd.call_args.kwargs
        assert "/tracking/shipments/42" in call_kwargs["url"]

    def test_request_body_is_passed_through(self):
        from app.main import app
        upstream_resp = _fake_httpx_response(200, b'{}')

        with patch("app.main.forward_request", new_callable=AsyncMock) as mock_fwd:
            mock_fwd.return_value = upstream_resp
            with TestClient(app, raise_server_exceptions=False) as client:
                # /auth/register is a public path — no token needed
                client.post(
                    "/auth/register",
                    content=b'{"username":"alice"}',
                    headers={"content-type": "application/json"},
                )

        call_kwargs = mock_fwd.call_args.kwargs
        assert call_kwargs["body"] == b'{"username":"alice"}'

    def test_authorization_header_is_forwarded(self):
        from app.main import app
        upstream_resp = _fake_httpx_response(200, b'{}')
        valid_token = _make_valid_token()

        with patch("app.main.forward_request", new_callable=AsyncMock) as mock_fwd:
            mock_fwd.return_value = upstream_resp
            with TestClient(app, raise_server_exceptions=False) as client:
                client.get(
                    "/auth/profile",
                    headers={"authorization": f"Bearer {valid_token}"},
                )

        call_kwargs = mock_fwd.call_args.kwargs
        assert call_kwargs["headers"].get("authorization") == f"Bearer {valid_token}"

    def test_query_params_are_forwarded(self):
        from app.main import app
        upstream_resp = _fake_httpx_response(200, b'[]')

        with patch("app.main.forward_request", new_callable=AsyncMock) as mock_fwd:
            mock_fwd.return_value = upstream_resp
            with TestClient(app, raise_server_exceptions=False) as client:
                client.get(
                    "/tracking/live?vehicle_id=7&limit=5",
                    headers=_auth_headers(),
                )

        call_kwargs = mock_fwd.call_args.kwargs
        assert call_kwargs["params"]["vehicle_id"] == "7"
        assert call_kwargs["params"]["limit"] == "5"


class TestProxyRouterErrors:

    def test_unknown_path_returns_404(self):
        from app.main import app
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/payments/invoice", headers=_auth_headers())
        assert response.status_code == 404
        assert "payments/invoice" in response.json()["detail"]

    def test_upstream_error_returns_502(self):
        from app.main import app
        from app.proxy import ProxyUpstreamError

        with patch("app.main.forward_request", new_callable=AsyncMock) as mock_fwd:
            mock_fwd.side_effect = ProxyUpstreamError("Connection refused")
            with TestClient(app, raise_server_exceptions=False) as client:
                # /auth/login is a public path — no token needed
                response = client.get("/auth/login")

        assert response.status_code == 502
        assert "upstream" in response.json()["detail"].lower()

    def test_upstream_500_is_passed_through(self):
        from app.main import app
        upstream_resp = _fake_httpx_response(500, b'{"error":"internal"}')

        with patch("app.main.forward_request", new_callable=AsyncMock) as mock_fwd:
            mock_fwd.return_value = upstream_resp
            with TestClient(app, raise_server_exceptions=False) as client:
                # /auth/login is a public path — no token needed
                response = client.get("/auth/login")

        assert response.status_code == 500

    def test_health_endpoint_is_not_proxied(self):
        from app.main import app
        with patch("app.main.forward_request", new_callable=AsyncMock) as mock_fwd:
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.get("/health")
        assert response.status_code == 200
        mock_fwd.assert_not_awaited()
