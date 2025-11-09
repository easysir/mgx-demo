from fastapi import APIRouter, Depends, HTTPException

from app.dependencies.auth import get_current_user
from app.models import ChatTurn, Message, MessageCreate, UserProfile
from app.services import agent_runtime_gateway, session_store

router = APIRouter()


@router.post("/messages", response_model=ChatTurn, status_code=201)
async def send_message(payload: MessageCreate, user: UserProfile = Depends(get_current_user)) -> ChatTurn:
    session = session_store.get_session(payload.session_id, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_message = session_store.append_message(
        session_id=payload.session_id,
        sender='user',
        content=payload.content,
        owner_id=user.id,
    )
    responses = await agent_runtime_gateway.handle_user_turn(
        session_id=payload.session_id,
        owner_id=session.owner_id,
        user_id=user.id,
        user_message=payload.content,
    )
    return ChatTurn(user=user_message, responses=responses)


@router.get("/messages/{session_id}", response_model=list[Message])
async def fetch_messages(session_id: str, user: UserProfile = Depends(get_current_user)) -> list[Message]:
    session = session_store.get_session(session_id, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.messages
