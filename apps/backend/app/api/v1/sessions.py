from fastapi import APIRouter, Depends, HTTPException

from app.dependencies.auth import get_current_user
from app.models import Message, SessionCreate, SessionResponse, UserProfile
from app.services.store import session_store

router = APIRouter()


@router.get("", response_model=list[SessionResponse])
async def list_sessions(user: UserProfile = Depends(get_current_user)) -> list[SessionResponse]:
    return session_store.list_sessions(user.id)


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    payload: SessionCreate | None = None,
    user: UserProfile = Depends(get_current_user),
) -> SessionResponse:
    """Create a new chat session."""
    session = session_store.create_session(owner_id=user.id, payload=payload)
    return session


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, user: UserProfile = Depends(get_current_user)) -> SessionResponse:
    session = session_store.get_session(session_id, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/{session_id}/messages", response_model=list[Message])
async def list_messages(session_id: str, user: UserProfile = Depends(get_current_user)) -> list[Message]:
    session = session_store.get_session(session_id, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.messages
