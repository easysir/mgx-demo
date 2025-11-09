from fastapi import Header, HTTPException, status

from app.models import UserProfile
from app.services import auth_service


def get_current_user(authorization: str | None = Header(default=None)) -> UserProfile:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")
    token = authorization.split(" ", 1)[1]
    return auth_service.get_profile(token)

