import os

from fastapi import Request
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

SECRET_KEY: str = os.environ["JWT_SECRET"]
ALGORITHM = "HS256"

# Bu path'ler token kontrolü olmadan geçer
PUBLIC_PATHS = {"/auth/register", "/auth/login", "/health", "/metrics"}


class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or malformed Authorization header"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header.removeprefix("Bearer ")
        try:
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)
