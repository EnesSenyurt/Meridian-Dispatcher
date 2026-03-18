import httpx
from typing import Any

# Upstream servislere asla iletilmemesi gereken hop-by-hop başlıkları
STRIPPED_HEADERS = {"host", "connection", "transfer-encoding", "content-length", "keep-alive"}


class ProxyUpstreamError(Exception):
    """Upstream servise ulaşılamadığında veya zaman aşımı oluştuğunda fırlatılır."""
    pass


async def forward_request(
    method: str,
    url: str,
    headers: dict[str, str],
    body: bytes,
    params: dict[str, Any],
) -> httpx.Response:
    """
    HTTP isteğini upstream servise iletir ve yanıtı döner.
    Ağ hatalarında ProxyUpstreamError fırlatır.
    """
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
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        raise ProxyUpstreamError(str(exc)) from exc
