"""Storage abstractions for session context state and snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Protocol

from ..context.models import ActionLogEntry, SessionContext, TodoEntry


@dataclass
class SessionState:
    action_log: list[ActionLogEntry] = field(default_factory=list)
    pending_todos: list[TodoEntry] = field(default_factory=list)
    agent_specific: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class SessionStateStore(Protocol):
    def load_state(self, session_id: str) -> SessionState: ...

    def persist_state(self, session_id: str, state: SessionState) -> None: ...

    def persist_action_detail(self, session_id: str, step_id: int, payload: Dict[str, Any]) -> str: ...

    def persist_session_context_snapshot(
        self,
        session_id: str,
        snapshot: SessionContext,
        step_id: int,
    ) -> str: ...

    def clear_session_state(self, session_id: str) -> None: ...


_STATE_STORE: SessionStateStore | None = None


def set_session_state_store(store: SessionStateStore) -> None:
    global _STATE_STORE
    _STATE_STORE = store


def get_session_state_store() -> SessionStateStore:
    global _STATE_STORE
    if _STATE_STORE is None:
        from .file_session_state_store import FileSessionStateStore

        _STATE_STORE = FileSessionStateStore()
    return _STATE_STORE


__all__ = [
    'SessionState',
    'SessionStateStore',
    'set_session_state_store',
    'get_session_state_store',
]
