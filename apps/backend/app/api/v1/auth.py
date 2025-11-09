from fastapi import APIRouter, HTTPException, status

from app.models import LoginRequest, TokenResponse, UserProfile
from app.services import auth_service

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    return auth_service.login(payload)


@router.get("/me", response_model=UserProfile)
async def profile(token: str) -> UserProfile:
    return auth_service.get_profile(token)


@router.post("/oauth/{provider}")
async def oauth_placeholder(provider: str) -> dict[str, str]:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=f"{provider} 登录尚未开放，敬请期待")
