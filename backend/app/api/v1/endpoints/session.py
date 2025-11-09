from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from app.services.session_manager import SessionManager, Session
from app.dependencies import get_session_manager

router = APIRouter()

@router.post("/sessions", response_model=Session, status_code=201)
async def create_session_endpoint(
    user_id: str,
    project_id: Optional[str] = None,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Create a new session for a user.
    """
    session = await session_manager.create_session(user_id=user_id, project_id=project_id)
    return session

@router.get("/sessions/{session_id}", response_model=Session)
async def get_session_endpoint(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Get a session by its ID.
    """
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session