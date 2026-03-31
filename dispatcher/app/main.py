from fastapi import FastAPI, Request
from fastapi.responses import Response, JSONResponse
from .database import db
from .config import resolve_upstream
from .proxy import forward_request, ProxyUpstreamError, ProxyTimeoutError
from .middleware import JWTAuthMiddleware

app = FastAPI(title="Dispatcher Gateway")
app.add_middleware(JWTAuthMiddleware)


@app.on_event("startup")
async def startup_event():
    await db.connect()


@app.on_event("shutdown")
async def shutdown_event():
    await db.disconnect()


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
