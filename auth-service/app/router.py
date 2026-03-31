from fastapi import APIRouter, Header, Depends
from .models import LoginRequest, RegisterRequest, TokenResponse, UserInfo
from .repository import BaseUserRepository, get_user_repository
from .service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

def get_auth_service(repo: BaseUserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(repo)

@router.post("/register", status_code=201)
async def register(body: RegisterRequest, service: AuthService = Depends(get_auth_service)):
    return await service.register(body)

@router.post("/login", status_code=200, response_model=TokenResponse)
async def login(body: LoginRequest, service: AuthService = Depends(get_auth_service)):
    return await service.login(body)

@router.get("/verify", status_code=200, response_model=UserInfo)
async def verify(authorization: str = Header(...), service: AuthService = Depends(get_auth_service)):
    return await service.verify_token(authorization)
