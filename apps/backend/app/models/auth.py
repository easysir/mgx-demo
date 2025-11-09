from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class UserProfile(BaseModel):
    id: str
    email: EmailStr
    name: str
    credits: int
    plan: str


class Token(BaseModel):
    token: str
    user: UserProfile
    issued_at: datetime
    expires_at: datetime

    @classmethod
    def create(cls, user: UserProfile, ttl_seconds: int = 3600) -> "Token":
        now = datetime.utcnow()
        return cls(
            token=f"token-{user.id}",
            user=user,
            issued_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds),
        )

