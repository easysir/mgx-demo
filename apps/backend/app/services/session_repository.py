from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi.encoders import jsonable_encoder

from app.models.chat import AgentRole, Message, SenderRole, Session, SessionCreate


class SessionRepository(ABC):
    @abstractmethod
    def create_session(self, owner_id: str, payload: Optional[SessionCreate] = None) -> Session: ...

    @abstractmethod
    def get_session(self, session_id: str, owner_id: Optional[str] = None) -> Optional[Session]: ...

    @abstractmethod
    def list_sessions(self, owner_id: str) -> List[Session]: ...

    @abstractmethod
    def list_messages(self, session_id: str, owner_id: str) -> List[Message]: ...

    @abstractmethod
    def append_message(
        self,
        *,
        session_id: str,
        sender: SenderRole,
        content: str,
        agent: Optional[AgentRole] = None,
        owner_id: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> Message: ...

    @abstractmethod
    def delete_session(self, session_id: str) -> None: ...


class InMemorySessionRepository(SessionRepository):
    def __init__(self) -> None:
        self._sessions: Dict[str, Session] = {}

    def create_session(self, owner_id: str, payload: Optional[SessionCreate] = None) -> Session:
        session_id = str(uuid4())
        initial_title = payload.title if payload and payload.title else f'Session {session_id[:8]}'
        session = Session(
            id=session_id,
            title=initial_title,
            created_at=datetime.utcnow(),
            owner_id=owner_id,
        )
        self._sessions[session_id] = session
        logger.debug('Created in-memory session %s for owner %s', session_id, owner_id)
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
            agent=agent,
        )
        session.messages.append(message)
        logger.debug('Appended in-memory message %s (%s) to session %s', message.id, sender, session_id)
        return message

    def delete_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


class FileSessionRepository(SessionRepository):
    def __init__(self, base_path: Optional[Path] = None) -> None:
        default_root = Path(os.getenv('SESSION_DATA_PATH', './data/sessions'))
        self.base_path = (base_path or default_root).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.index_path = self.base_path / 'index.json'
        self._lock = Lock()
        self._index = self._load_index()

    def create_session(self, owner_id: str, payload: Optional[SessionCreate] = None) -> Session:
        session_id = str(uuid4())
        initial_title = payload.title if payload and payload.title else f'Session {session_id[:8]}'
        session = Session(
            id=session_id,
            title=initial_title,
            created_at=datetime.utcnow(),
            owner_id=owner_id,
            messages=[],
        )
        with self._lock:
            self._save_session(session)
            owners = self._index.setdefault('owners', {})
            owner_sessions = owners.setdefault(owner_id, [])
            owner_sessions.insert(0, session_id)
            self._write_index()
        logger.info('Created file-backed session %s for owner %s', session_id, owner_id)
        return session

    def get_session(self, session_id: str, owner_id: Optional[str] = None) -> Optional[Session]:
        session = self._load_session(session_id)
        if session and owner_id and session.owner_id != owner_id:
            return None
        return session

    def list_sessions(self, owner_id: str) -> List[Session]:
        owners = self._index.get('owners', {})
        session_ids = owners.get(owner_id, [])
        sessions: List[Session] = []
        for session_id in session_ids:
            session = self._load_session(session_id)
            if session:
                if session.title.startswith('Session '):
                    first_user = next((m for m in session.messages if m.sender == 'user'), None)
                    if first_user:
                        session.title = first_user.content[:60] or session.title
                sessions.append(session)
        return sessions

    def list_messages(self, session_id: str, owner_id: str) -> List[Message]:
        session = self.get_session(session_id, owner_id)
        return session.messages if session else []

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
        with self._lock:
            session = self.get_session(session_id, owner_id)
            if not session:
                raise KeyError(f'Session {session_id} not found')
            if session.title.startswith('Session ') and sender == 'user':
                session.title = content[:60] or session.title
            message = Message(
                id=message_id or str(uuid4()),
                session_id=session_id,
                sender=sender,
                content=content,
                timestamp=datetime.utcnow(),
                agent=agent,
            )
            session.messages.append(message)
            self._save_session(session)
            logger.info('Persisted message %s (%s) to session %s', message.id, sender, session_id)
            return message

    def delete_session(self, session_id: str) -> None:
        with self._lock:
            path = self._session_path(session_id)
            if path.exists():
                path.unlink()
            owners = self._index.get('owners', {})
            for owner_sessions in owners.values():
                if session_id in owner_sessions:
                    owner_sessions.remove(session_id)
            self._write_index()

    def _session_path(self, session_id: str) -> Path:
        return self.base_path / f'{session_id}.json'

    def _save_session(self, session: Session) -> None:
        data = jsonable_encoder(session)
        path = self._session_path(session.id)
        tmp = path.with_suffix('.tmp')
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        tmp.replace(path)

    def _load_session(self, session_id: str) -> Optional[Session]:
        path = self._session_path(session_id)
        if not path.exists():
            return None
        raw = json.loads(path.read_text())
        try:
            return Session.model_validate(raw)
        except Exception:
            return None

    def _load_index(self) -> Dict[str, Dict[str, List[str]]]:
        if not self.index_path.exists():
            return {'owners': {}}
        try:
            return json.loads(self.index_path.read_text())
        except Exception:
            return {'owners': {}}

    def _write_index(self) -> None:
        tmp = self.index_path.with_suffix('.tmp')
        tmp.write_text(json.dumps(self._index, ensure_ascii=False, indent=2))
        tmp.replace(self.index_path)


def _build_repository() -> SessionRepository:
    backend = os.getenv('SESSION_STORAGE_BACKEND', 'file').lower()
    if backend == 'file':
        return FileSessionRepository()
    return InMemorySessionRepository()


session_repository = _build_repository()
logger = logging.getLogger('session_repository')
