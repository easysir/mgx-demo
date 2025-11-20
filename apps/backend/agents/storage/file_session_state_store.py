"""File-backed SessionStateStore implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from ..context.models import ActionLogEntry, SessionContext, TodoEntry
from .session_state_store import SessionState, SessionStateStore


class FileSessionStateStore(SessionStateStore):
    """Default store writing session state to the data/sessions directory."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self._base_dir = base_dir or Path(__file__).resolve().parents[3] / 'data' / 'sessions'
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, SessionState] = {}

    def load_state(self, session_id: str) -> SessionState:
        cached = self._cache.get(session_id)
        if cached:
            return cached
        path = self._state_path(session_id)
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding='utf-8'))
            except json.JSONDecodeError:
                payload = {}
        else:
            payload = {}
        state = SessionState(
            action_log=[self._deserialize_action(item) for item in payload.get('action_log', [])],
            pending_todos=[self._deserialize_todo(item) for item in payload.get('pending_todos', [])],
            agent_specific=payload.get('agent_specific', {}),
        )
        self._cache[session_id] = state
        return state

    def persist_state(self, session_id: str, state: SessionState) -> None:
        payload = {
            'action_log': [self._serialize_action(entry) for entry in state.action_log],
            'pending_todos': [self._serialize_todo(entry) for entry in state.pending_todos],
            'agent_specific': state.agent_specific,
        }
        path = self._state_path(session_id)
        tmp_path = path.with_suffix('.tmp')
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        tmp_path.replace(path)
        self._cache[session_id] = state

    def persist_action_detail(self, session_id: str, step_id: int, payload: Dict[str, Any]) -> str:
        directory = self._step_dir(session_id)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f'step_{step_id}.json'
        tmp_path = path.with_suffix('.tmp')
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        tmp_path.replace(path)
        return str(path)

    def persist_session_context_snapshot(self, session_id: str, snapshot: SessionContext, step_id: int) -> str:
        directory = self._snapshot_dir(session_id)
        directory.mkdir(parents=True, exist_ok=True)
        payload = {
            'session_id': snapshot.session_id,
            'owner_id': snapshot.owner_id,
            'user_id': snapshot.user_id,
            'user_messages': snapshot.user_message,
            'most_recent_user_message': snapshot.most_recent_user_message,
            'conversation_history': snapshot.conversation_history,
            'artifacts': snapshot.artifacts,
            'files_overview': snapshot.files_overview,
            'action_log': [self._serialize_action(entry) for entry in snapshot.action_log],
            'pending_todos': [self._serialize_todo(entry) for entry in snapshot.pending_todos],
            'agent_specific': snapshot.agent_specific,
        }
        path = directory / f'step_{step_id}.json'
        tmp_path = path.with_suffix('.tmp')
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        tmp_path.replace(path)
        return str(path)

    def clear_session_state(self, session_id: str) -> None:
        self._cache.pop(session_id, None)
        path = self._state_path(session_id)
        if path.exists():
            path.unlink()

    def _state_path(self, session_id: str) -> Path:
        return self._base_dir / f'{session_id}_context.json'

    def _step_dir(self, session_id: str) -> Path:
        return self._base_dir / f'{session_id}_steps'

    def _snapshot_dir(self, session_id: str) -> Path:
        return self._base_dir / f'{session_id}_context_snapshots'

    @staticmethod
    def _serialize_action(entry: ActionLogEntry) -> Dict[str, Any]:
        return {
            'agent': entry.agent,
            'action': entry.action,
            'result': entry.result,
            'status': entry.status,
            'timestamp': entry.timestamp,
            'metadata': entry.metadata,
        }

    @staticmethod
    def _deserialize_action(data: Dict[str, Any]) -> ActionLogEntry:
        return ActionLogEntry(
            agent=data.get('agent', 'Mike'),
            action=data.get('action', ''),
            result=data.get('result', ''),
            status=data.get('status', 'success'),
            timestamp=data.get('timestamp'),
            metadata=data.get('metadata') or {},
        )

    @staticmethod
    def _serialize_todo(entry: TodoEntry) -> Dict[str, Any]:
        return {
            'description': entry.description,
            'owner': entry.owner,
            'priority': entry.priority,
            'status': entry.status,
            'timestamp': entry.timestamp,
            'metadata': entry.metadata,
        }

    @staticmethod
    def _deserialize_todo(data: Dict[str, Any]) -> TodoEntry:
        return TodoEntry(
            description=data.get('description', ''),
            owner=data.get('owner', 'system'),
            priority=data.get('priority', 'medium'),
            status=data.get('status', 'pending'),
            timestamp=data.get('timestamp'),
            metadata=data.get('metadata') or {},
        )


__all__ = ['FileSessionStateStore']
