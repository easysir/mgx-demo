from datetime import datetime
from typing import Dict, Optional

from fastapi import HTTPException, status

from app.models import LoginRequest, TokenResponse, UserProfile


class AuthService:
    """Simple in-memory auth for MVP (single hardcoded user)."""

    def __init__(self) -> None:
        self._users: Dict[str, dict] = {
            "demo@mgx.dev": {
                "password": "mgx-demo",
                "profile": UserProfile(id="user-1", email="demo@mgx.dev", name="Harvey Yang", credits=1204, plan="Pro"),
            },
            "linda@mgx.dev": {
                "password": "mgx-linda",
                "profile": UserProfile(id="user-2", email="linda@mgx.dev", name="Linda Chen", credits=680, plan="Basic"),
            },
        }
        self._tokens: Dict[str, dict] = {}

    def login(self, payload: LoginRequest) -> TokenResponse:
        record = self._users.get(payload.email)
        if not record or record["password"] != payload.password:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        token = f"token-{record['profile'].id}"
        self._tokens[token] = {
            "user": record["profile"],
            "issued_at": datetime.utcnow(),
        }
        return TokenResponse(access_token=token)

    def get_profile(self, token: str) -> UserProfile:
        record = self._tokens.get(token)
        if not record:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return record["user"]


auth_service = AuthService()
