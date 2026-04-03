import asyncio

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError
from jose import JWTError
from .repository import BaseUserRepository
from .models import RegisterRequest, LoginRequest, TokenResponse, UserInfo
from .auth_utils import create_access_token, decode_token, hash_password, verify_password

class AuthService:
    def __init__(self, repository: BaseUserRepository):
        self.repository = repository

    async def register(self, body: RegisterRequest) -> dict:
        existing = await self.repository.find_by_email(body.email)
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")

        loop = asyncio.get_event_loop()
        hashed = await loop.run_in_executor(None, hash_password, body.password)
        doc = {"email": body.email, "password_hash": hashed, "role": body.role}

        try:
            result = await self.repository.create_user(doc)
        except DuplicateKeyError:
            raise HTTPException(status_code=409, detail="Email already registered")

        return {
            "user_id": str(result.inserted_id), 
            "email": body.email, 
            "role": body.role,
            "_links": {
                "self": "/auth/register",
                "login": "/auth/login"
            }
        }

    async def login(self, body: LoginRequest) -> TokenResponse:
        user = await self.repository.find_by_email(body.email)
        if not user or not verify_password(body.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token(str(user["_id"]), user["email"], user["role"])
        return TokenResponse(
            access_token=token,
            links={
                "self": "/auth/login",
                "verify": "/auth/verify"
            }
        )

    async def verify_token(self, authorization: str) -> UserInfo:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing Bearer token")

        token = authorization.removeprefix("Bearer ")
        try:
            payload = decode_token(token)
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        return UserInfo(
            user_id=payload["sub"],
            email=payload["email"],
            role=payload["role"],
            links={
                "self": "/auth/verify",
                "deliveries": "/delivery"
            }
        )
