import httpx
from typing import Any

# hop-by-hop başlıkları
STRIPPED_HEADERS = {"host", "connection", "transfer-encoding", "content-length", "keep-alive"}


class ProxyUpstreamError(Exception):
    pass


class ProxyTimeoutError(Exception):
    pass


async def forward_request(
    method: str,
    url: str,
    headers: dict[str, str],
    body: bytes,
    params: dict[str, Any],
) -> httpx.Response:
    clean_headers = {
        k: v for k, v in headers.items()
        if k.lower() not in STRIPPED_HEADERS
    }

    try:
        async with httpx.AsyncClient() as client:
            return await client.request(
                method=method,
                url=url,
                headers=clean_headers,
                content=body,
                params=params,
            )
    except httpx.TimeoutException as exc:
        raise ProxyTimeoutError(str(exc)) from exc
    except httpx.ConnectError as exc:
        raise ProxyUpstreamError(str(exc)) from exc
