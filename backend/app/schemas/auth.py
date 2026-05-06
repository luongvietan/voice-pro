from __future__ import annotations

import re
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class GoogleOAuthRequest(BaseModel):
    access_token: str = Field(..., min_length=10)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class UserSummary(BaseModel):
    id: UUID
    email: str | None
    display_name: str | None
    avatar_url: str | None
    balance_minutes: int
    is_paid: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str | None = None
    user: UserSummary
