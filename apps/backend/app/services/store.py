from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from app.models.chat import ChatTurn, Message, Session, SessionCreate, SenderRole, AgentRole


class SessionStore:
    """Very lightweight in-memory store for sessions/messages (MVP only)."""

    def __init__(self) -> None:
        self._sessions: Dict[str, Session] = {}

    def create_session(self, owner_id: str, payload: Optional[SessionCreate] = None) -> Session:
        session_id = str(uuid4())
        session = Session(
            id=session_id,
            title=payload.title if payload and payload.title else f'Session {session_id[:8]}',
            created_at=datetime.utcnow(),
            owner_id=owner_id,
        )
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str, owner_id: Optional[str] = None) -> Optional[Session]:
        session = self._sessions.get(session_id)
        if session and owner_id and session.owner_id != owner_id:
            return None
        return session

    def list_messages(self, session_id: str, owner_id: str) -> List[Message]:
        session = self.get_session(session_id, owner_id)
        return session.messages if session else []

    def list_sessions(self, owner_id: str) -> List[Session]:
        return [session for session in self._sessions.values() if session.owner_id == owner_id]

    def append_message(
        self,
        *,
        session_id: str,
        sender: SenderRole,
        content: str,
        agent: Optional[AgentRole] = None,
        owner_id: Optional[str] = None,
    ) -> Message:
        session = self.get_session(session_id, owner_id)
        if not session:
            raise KeyError(f'Session {session_id} not found')

        message = Message(
            id=str(uuid4()),
            session_id=session_id,
            sender=sender,
            content=content,
            timestamp=datetime.utcnow(),
            agent=agent
        )
        session.messages.append(message)
        return message

    def simulate_agent_response(self, session_id: str, user_content: str) -> ChatTurn:
        session = self.get_session(session_id)
        if not session:
            raise KeyError(f'Session {session_id} not found')

        user_message = self.append_message(
            session_id=session_id, sender='user', content=user_content, owner_id=session.owner_id
        )

        # Simple stub: Mike acknowledges then Alex follows up.
        responses: List[Message] = [
            self.append_message(
                session_id=session_id,
                sender='status',
                agent='Mike',
                content='Mike 正在评估任务，准备调度团队。',
                owner_id=session.owner_id,
            ),
            self.append_message(
                session_id=session_id,
                sender='mike',
                agent='Mike',
                content='Mike：需求已记录，稍后将安排 Bob/ Alex 分别处理架构与开发。',
                owner_id=session.owner_id,
            ),
            self.append_message(
                session_id=session_id,
                sender='status',
                agent='Alex',
                content='Alex 已接手任务，开始修改代码。',
                owner_id=session.owner_id,
            ),
            self.append_message(
                session_id=session_id,
                sender='agent',
                agent='Alex',
                content='Alex：代码变更完成，如需微调配色请继续提示。',
                owner_id=session.owner_id,
            )
        ]
        return ChatTurn(user=user_message, responses=responses)


session_store = SessionStore()
