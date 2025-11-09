from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.services.session_manager import SessionManager
from app.dependencies import get_session_manager, get_agent_manager
from app.services.agent_manager import AgentManager

router = APIRouter()

class ChatMessage(BaseModel):
    session_id: str
    message: str

@router.post("/chat/message")
async def post_message(
    chat_message: ChatMessage,
    session_manager: SessionManager = Depends(get_session_manager),
    agent_manager: AgentManager = Depends(get_agent_manager)
):
    """
    Receives a user message and routes it to the MikeAgent for processing.
    """
    session = await session_manager.get_session(chat_message.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get the MikeAgent instance for this session
    mike_agent = agent_manager.get_agent_instance("mike", chat_message.session_id)
    
    # Run the MikeAgent with the user's message
    result = await mike_agent.run(user_requirement=chat_message.message)
    
    return {"response": result}