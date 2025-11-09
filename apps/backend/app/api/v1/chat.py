from fastapi import APIRouter, Depends, HTTPException

from app.dependencies.auth import get_current_user
from app.models import ChatTurn, Message, MessageCreate, UserProfile
from app.services.store import session_store

router = APIRouter()


@router.post("/messages", response_model=ChatTurn, status_code=201)
async def send_message(payload: MessageCreate, user: UserProfile = Depends(get_current_user)) -> ChatTurn:
    session = session_store.get_session(payload.session_id, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    turn = session_store.simulate_agent_response(session_id=payload.session_id, user_content=payload.content)
    return turn


@router.get("/messages/{session_id}", response_model=list[Message])
async def fetch_messages(session_id: str, user: UserProfile = Depends(get_current_user)) -> list[Message]:
    session = session_store.get_session(session_id, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.messages
