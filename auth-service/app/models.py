from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: Literal["sender", "courier"]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    model_config = {"populate_by_name": True}
    access_token: str
    token_type: str = "bearer"
    links: dict = Field(default_factory=dict, alias="_links")


class UserInfo(BaseModel):
    model_config = {"populate_by_name": True}
    user_id: str
    email: str
    role: str
    links: dict = Field(default_factory=dict, alias="_links")
