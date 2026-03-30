from fastapi import APIRouter, Header, HTTPException
from jose import JWTError
from pymongo.errors import DuplicateKeyError

from .auth_utils import create_access_token, decode_token, hash_password, verify_password
from .database import db
from .models import LoginRequest, RegisterRequest, TokenResponse, UserInfo

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
async def register(body: RegisterRequest):
    existing = await db.execute("users", "find_one", {"email": body.email})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    hashed = hash_password(body.password)
    doc = {"email": body.email, "password_hash": hashed, "role": body.role}

    try:
        result = await db.execute("users", "insert_one", doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Email already registered")

    return {"user_id": str(result.inserted_id), "email": body.email, "role": body.role}


@router.post("/login", status_code=200, response_model=TokenResponse)
async def login(body: LoginRequest):
    user = await db.execute("users", "find_one", {"email": body.email})
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(str(user["_id"]), user["email"], user["role"])
    return TokenResponse(access_token=token)


@router.get("/verify", status_code=200, response_model=UserInfo)
async def verify(authorization: str = Header(...)):
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
    )
