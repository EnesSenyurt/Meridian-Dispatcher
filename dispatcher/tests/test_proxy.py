import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch


def _make_mock_response(status_code: int, headers: dict = None):
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.content = b'{"ok": true}'
    response.headers = httpx.Headers(headers or {"content-type": "application/json"})
    return response


class TestForwardRequestHappyPath:

    async def test_get_request_returns_upstream_status(self):
        from app.proxy import forward_request
        mock_response = _make_mock_response(200)

        with patch("app.proxy.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await forward_request(
                method="GET",
                url="http://auth-service:8000/auth/login",
                headers={"authorization": "Bearer token"},
                body=b"",
                params={},
            )

        assert result.status_code == 200
        mock_client.request.assert_awaited_once_with(
            method="GET",
            url="http://auth-service:8000/auth/login",
            headers={"authorization": "Bearer token"},
            content=b"",
            params={},
        )

    async def test_post_request_passes_body_bytes(self):
        from app.proxy import forward_request
        mock_response = _make_mock_response(201)

        with patch("app.proxy.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await forward_request(
                method="POST",
                url="http://delivery-service:8000/delivery/orders",
                headers={"content-type": "application/json"},
                body=b'{"item": "box"}',
                params={},
            )

        assert result.status_code == 201
        call_kwargs = mock_client.request.call_args.kwargs
        assert call_kwargs["content"] == b'{"item": "box"}'
        assert call_kwargs["method"] == "POST"

    async def test_query_params_are_forwarded(self):
        from app.proxy import forward_request
        mock_response = _make_mock_response(200)

        with patch("app.proxy.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            await forward_request(
                method="GET",
                url="http://tracking-service:8000/tracking/live",
                headers={},
                body=b"",
                params={"vehicle_id": "42", "limit": "10"},
            )

        call_kwargs = mock_client.request.call_args.kwargs
        assert call_kwargs["params"] == {"vehicle_id": "42", "limit": "10"}

    async def test_all_http_methods_pass_through(self):
        from app.proxy import forward_request

        for method in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
            mock_response = _make_mock_response(200)
            with patch("app.proxy.httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client.request = AsyncMock(return_value=mock_response)
                mock_client_cls.return_value = mock_client

                result = await forward_request(
                    method=method,
                    url="http://auth-service:8000/auth/test",
                    headers={},
                    body=b"",
                    params={},
                )
            assert result.status_code == 200


class TestForwardRequestErrors:

    async def test_connect_error_raises_proxy_upstream_error(self):
        from app.proxy import forward_request, ProxyUpstreamError

        with patch("app.proxy.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.request = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )
            mock_client_cls.return_value = mock_client

            with pytest.raises(ProxyUpstreamError):
                await forward_request(
                    method="GET",
                    url="http://auth-service:8000/auth/login",
                    headers={},
                    body=b"",
                    params={},
                )

    async def test_timeout_raises_proxy_timeout_error(self):
        from app.proxy import forward_request, ProxyTimeoutError

        with patch("app.proxy.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.request = AsyncMock(
                side_effect=httpx.TimeoutException("Timed out")
            )
            mock_client_cls.return_value = mock_client

            with pytest.raises(ProxyTimeoutError):
                await forward_request(
                    method="GET",
                    url="http://auth-service:8000/auth/login",
                    headers={},
                    body=b"",
                    params={},
                )

    async def test_hop_by_hop_headers_are_stripped(self):
        from app.proxy import forward_request, STRIPPED_HEADERS
        mock_response = _make_mock_response(200)

        with patch("app.proxy.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            dirty_headers = {
                "authorization": "Bearer token",
                "host": "dispatcher:8080",
                "connection": "keep-alive",
                "transfer-encoding": "chunked",
                "content-length": "42",
            }

            await forward_request(
                method="GET",
                url="http://auth-service:8000/auth/login",
                headers=dirty_headers,
                body=b"",
                params={},
            )

        forwarded_headers = mock_client.request.call_args.kwargs["headers"]
        for h in STRIPPED_HEADERS:
            assert h not in forwarded_headers
        assert "authorization" in forwarded_headers
