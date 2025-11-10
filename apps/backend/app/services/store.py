from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from app.models.chat import Message, Session, SessionCreate, SenderRole, AgentRole


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
        message_id: Optional[str] = None,
    ) -> Message:
        session = self.get_session(session_id, owner_id)
        if not session:
            raise KeyError(f'Session {session_id} not found')

        message = Message(
            id=message_id or str(uuid4()),
            session_id=session_id,
            sender=sender,
            content=content,
            timestamp=datetime.utcnow(),
            agent=agent
        )
        session.messages.append(message)
        return message

    def delete_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

session_store = SessionStore()
