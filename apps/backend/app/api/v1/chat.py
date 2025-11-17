from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder

from app.dependencies.auth import get_current_user
from app.models import ChatTurn, Message, MessageCreate, UserProfile
from app.services import agent_runtime_gateway, session_repository
from app.services.stream import stream_manager
from agents.llm import LLMProviderError
from agents.stream import message_event

router = APIRouter()


@router.post("/messages", response_model=ChatTurn, status_code=201)
async def send_message(payload: MessageCreate, user: UserProfile = Depends(get_current_user)) -> ChatTurn:
    session = session_repository.get_session(payload.session_id, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_message = session_repository.append_message(
        session_id=payload.session_id,
        sender='user',
        content=payload.content,
        owner_id=user.id,
    )
    await stream_manager.broadcast(
        payload.session_id,
        message_event(
            sender='user',
            agent=None,
            content=user_message.content,
            message_id=user_message.id,
            timestamp=jsonable_encoder(user_message.timestamp),
        ),
    )
    try:
        responses = await agent_runtime_gateway.handle_user_turn(
            session_id=payload.session_id,
            owner_id=session.owner_id,
            user_id=user.id,
            user_message=payload.content,
        )
        return ChatTurn(user=user_message, responses=responses)
    except LLMProviderError as exc:
        # Persist an error/status message so历史可追踪
        session_repository.append_message(
            session_id=payload.session_id,
            sender='status',
            content=f"LLM 调用失败：{exc}",
            owner_id=session.owner_id,
            agent='Mike'
        )
        raise HTTPException(status_code=429, detail=str(exc)) from exc


@router.get("/messages/{session_id}", response_model=list[Message])
async def fetch_messages(session_id: str, user: UserProfile = Depends(get_current_user)) -> list[Message]:
    session = session_repository.get_session(session_id, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.messages
