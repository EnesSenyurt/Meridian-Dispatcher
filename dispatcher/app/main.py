from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import Response, JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import httpx
import time
from datetime import datetime

from .database import db
from .config import resolve_upstream
from .proxy import forward_request, ProxyUpstreamError, ProxyTimeoutError
from .middleware import JWTAuthMiddleware
from .metrics import REQUEST_COUNT, REQUEST_LATENCY, ACTIVE_REQUESTS, LOG_ENTRY


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    async with httpx.AsyncClient(timeout=30.0, limits=httpx.Limits(max_connections=500, max_keepalive_connections=100)) as client:
        app.state.http_client = client
        yield
    await db.disconnect()


app = FastAPI(title="Dispatcher Gateway", lifespan=lifespan)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    if request.url.path in {"/metrics", "/health"}:
        return await call_next(request)

    service_name = "unknown"
    if request.url.path.startswith("/auth"):
        service_name = "auth"
    elif request.url.path.startswith("/delivery"):
        service_name = "delivery"
    elif request.url.path.startswith("/tracking"):
        service_name = "tracking"

    start_time = time.time()
    timestamp = datetime.now().isoformat()
    
    ACTIVE_REQUESTS.inc()
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception as exc:
        status_code = 500
        raise exc
    finally:
        ACTIVE_REQUESTS.dec()
        duration = time.time() - start_time
        REQUEST_COUNT.labels(method=request.method, service=service_name, status=str(status_code)).inc()
        REQUEST_LATENCY.labels(method=request.method, service=service_name, status=str(status_code)).observe(duration)
        
        dur_ms = f"{duration * 1000:.0f}ms"
        LOG_ENTRY.labels(
            timestamp=timestamp,
            method=request.method,
            path=request.url.path,
            status=str(status_code),
            duration_ms=dur_ms
        ).set(1)

app.add_middleware(JWTAuthMiddleware)

@app.get("/metrics")
async def get_metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)



@app.get("/health")
async def health_check():
    return {"status": "dispatcher is running"}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def reverse_proxy(request: Request, path: str):
    full_path = "/" + path
    upstream_url = resolve_upstream(full_path)

    if upstream_url is None:
        return JSONResponse(
            status_code=404,
            content={"detail": f"No route found for path: {full_path}"},
        )

    try:
        upstream_response = await forward_request(
            method=request.method,
            url=upstream_url,
            headers=dict(request.headers),
            body=await request.body(),
            params=dict(request.query_params),
            client=request.app.state.http_client,
        )
    except ProxyUpstreamError as exc:
        return JSONResponse(
            status_code=502,
            content={"detail": f"Upstream service unavailable: {exc}"},
        )
    except ProxyTimeoutError as exc:
        return JSONResponse(
            status_code=503,
            content={"detail": f"Upstream service timeout: {exc}"},
        )

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=dict(upstream_response.headers),
    )
