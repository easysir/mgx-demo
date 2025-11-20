"""Persistent session context state helpers (action log, todos, agent data)."""

from __future__ import annotations

from typing import Any, Dict, List

from shared.types import AgentRole

from ..storage import (
    SessionState,
    get_session_state_store,
)
from .models import ActionLogEntry, SessionContext, TodoEntry

_STATE_STORE = get_session_state_store()


def get_session_state(session_id: str) -> SessionState:
    return _STATE_STORE.load_state(session_id)


def hydrate_session_context(
    *,
    session_id: str,
    owner_id: str,
    user_id: str,
    user_messages: List[str],
    most_recent_user_message: str,
    history: str,
    artifacts: str,
    files_overview: str,
) -> SessionContext:
    # 将持久化状态与即时采集的 history/files 等拼接成 SessionContext
    state = _STATE_STORE.load_state(session_id)
    return SessionContext(
        session_id=session_id,
        owner_id=owner_id,
        user_id=user_id,
        user_message=list(user_messages),
        most_recent_user_message=most_recent_user_message,
        conversation_history=history,
        artifacts=artifacts,
        files_overview=files_overview,
        action_log=list(state.action_log),
        pending_todos=list(state.pending_todos),
        agent_specific=state.agent_specific.copy(),
    )


def persist_action_detail(session_id: str, step_id: int, payload: Dict[str, Any]) -> str:
    """将完整步骤详情持久化，返回文件路径，供后续索引。"""

    return _STATE_STORE.persist_action_detail(session_id, step_id, payload)


def persist_session_context_snapshot(session_id: str, snapshot: SessionContext, step_id: int) -> str:
    """持久化当前 SessionContext，以便后续复盘时直接查看指定步骤的上下文。"""

    return _STATE_STORE.persist_session_context_snapshot(session_id, snapshot, step_id)


def record_action(session_id: str, entry: ActionLogEntry) -> None:
    # 只保留最近 10 条关键动作，避免文件无限增长
    state = _STATE_STORE.load_state(session_id)
    state.action_log.append(entry)
    state.action_log = state.action_log[-10:]
    _STATE_STORE.persist_state(session_id, state)


def attach_snapshot_to_last_action(session_id: str, snapshot_path: str) -> None:
    """为刚记录的 action_log 绑定上下文快照路径，方便后续 timeline 直接索引。"""
    state = _STATE_STORE.load_state(session_id)
    if not state.action_log:
        return
    entry = state.action_log[-1]
    metadata = entry.metadata or {}
    metadata['context_snapshot'] = snapshot_path
    entry.metadata = metadata
    _STATE_STORE.persist_state(session_id, state)


def add_todo(session_id: str, todo: TodoEntry) -> None:
    # 新增 TODO 时也限制列表长度，重点展示近期待办
    state = _STATE_STORE.load_state(session_id)
    state.pending_todos.append(todo)
    if len(state.pending_todos) > 20:
        state.pending_todos = state.pending_todos[-20:]
    _STATE_STORE.persist_state(session_id, state)


def update_todo_status(session_id: str, description: str, status: str) -> None:
    # 简单按 description 匹配并更新状态
    state = _STATE_STORE.load_state(session_id)
    for item in state.pending_todos:
        if item.description == description:
            item.status = status
            break
    _STATE_STORE.persist_state(session_id, state)


def put_agent_data(session_id: str, agent: AgentRole, data: Dict[str, Any]) -> None:
    # Agent-specific 数据用 dict 存储，可写入个性化提示
    state = _STATE_STORE.load_state(session_id)
    state.agent_specific[agent] = data
    _STATE_STORE.persist_state(session_id, state)


def clear_session_state(session_id: str) -> None:
    # 会话结束/重置时清除缓存与落盘文件
    _STATE_STORE.clear_session_state(session_id)


__all__ = [
    'SessionState',
    'get_session_state',
    'hydrate_session_context',
    'persist_action_detail',
    'persist_session_context_snapshot',
    'record_action',
    'attach_snapshot_to_last_action',
    'add_todo',
    'update_todo_status',
    'put_agent_data',
    'clear_session_state',
]
