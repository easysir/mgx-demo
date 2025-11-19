"""Persistent session context state helpers (action log, todos, agent data)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from shared.types import AgentRole

from .models import ActionLogEntry, SessionContext, TodoEntry

# 会话级上下文状态全部落在 data/sessions 目录，供 Agents 跨轮次共享
_STATE_DIR = Path(__file__).resolve().parents[3] / 'data' / 'sessions'
_STATE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class SessionState:
    action_log: List[ActionLogEntry] = field(default_factory=list)
    pending_todos: List[TodoEntry] = field(default_factory=list)
    agent_specific: Dict[AgentRole, Dict[str, Any]] = field(default_factory=dict)


# 内存缓存避免每次都从磁盘解析 JSON
_STATE_CACHE: Dict[str, SessionState] = {}


def _state_path(session_id: str) -> Path:
    # 每个 session 独立一个 context.json 文件
    return _STATE_DIR / f'{session_id}_context.json'


def _serialize_action(entry: ActionLogEntry) -> Dict[str, Any]:
    # 将 dataclass 转为可 JSON 序列化的 dict
    return {
        'agent': entry.agent,
        'action': entry.action,
        'result': entry.result,
        'status': entry.status,
        'timestamp': entry.timestamp,
        'metadata': entry.metadata,
    }


def _deserialize_action(data: Dict[str, Any]) -> ActionLogEntry:
    # 反序列化时提供默认值，防止旧版本字段缺失
    return ActionLogEntry(
        agent=data.get('agent', 'Mike'),
        action=data.get('action', ''),
        result=data.get('result', ''),
        status=data.get('status', 'success'),
        timestamp=data.get('timestamp'),
        metadata=data.get('metadata') or {},
    )


def _serialize_todo(entry: TodoEntry) -> Dict[str, Any]:
    # TODO 同理需要完整字段
    return {
        'description': entry.description,
        'owner': entry.owner,
        'priority': entry.priority,
        'status': entry.status,
        'timestamp': entry.timestamp,
        'metadata': entry.metadata,
    }


def _deserialize_todo(data: Dict[str, Any]) -> TodoEntry:
    # 兼容遗留数据：owner/priority/status 均可缺省
    return TodoEntry(
        description=data.get('description', ''),
        owner=data.get('owner', 'system'),
        priority=data.get('priority', 'medium'),
        status=data.get('status', 'pending'),
        timestamp=data.get('timestamp'),
        metadata=data.get('metadata') or {},
    )


def _load_state(session_id: str) -> SessionState:
    # 尝试命中缓存，未命中则从 JSON 恢复
    cached = _STATE_CACHE.get(session_id)
    if cached:
        return cached
    path = _state_path(session_id)
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            payload = {}
    else:
        payload = {}
    state = SessionState(
        action_log=[_deserialize_action(item) for item in payload.get('action_log', [])],
        pending_todos=[_deserialize_todo(item) for item in payload.get('pending_todos', [])],
        agent_specific=payload.get('agent_specific', {}),
    )
    _STATE_CACHE[session_id] = state
    return state


def _persist_state(session_id: str, state: SessionState) -> None:
    payload = {
        'action_log': [_serialize_action(entry) for entry in state.action_log],
        'pending_todos': [_serialize_todo(entry) for entry in state.pending_todos],
        'agent_specific': state.agent_specific,
    }
    path = _state_path(session_id)
    tmp_path = path.with_suffix('.tmp')
    # 先写临时文件再覆盖，避免并发时文件损坏
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp_path.replace(path)


def get_session_state(session_id: str) -> SessionState:
    return _load_state(session_id)


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
    state = _load_state(session_id)
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


def record_action(session_id: str, entry: ActionLogEntry) -> None:
    # 只保留最近 10 条关键动作，避免文件无限增长
    state = _load_state(session_id)
    state.action_log.append(entry)
    state.action_log = state.action_log[-10:]
    _persist_state(session_id, state)


def add_todo(session_id: str, todo: TodoEntry) -> None:
    # 新增 TODO 时也限制列表长度，重点展示近期待办
    state = _load_state(session_id)
    state.pending_todos.append(todo)
    if len(state.pending_todos) > 20:
        state.pending_todos = state.pending_todos[-20:]
    _persist_state(session_id, state)


def update_todo_status(session_id: str, description: str, status: str) -> None:
    # 简单按 description 匹配并更新状态
    state = _load_state(session_id)
    for item in state.pending_todos:
        if item.description == description:
            item.status = status
            break
    _persist_state(session_id, state)


def put_agent_data(session_id: str, agent: AgentRole, data: Dict[str, Any]) -> None:
    # Agent-specific 数据用 dict 存储，可写入个性化提示
    state = _load_state(session_id)
    state.agent_specific[agent] = data
    _persist_state(session_id, state)


def clear_session_state(session_id: str) -> None:
    # 会话结束/重置时清除缓存与落盘文件
    _STATE_CACHE.pop(session_id, None)
    path = _state_path(session_id)
    if path.exists():
        path.unlink()


__all__ = [
    'SessionState',
    'get_session_state',
    'hydrate_session_context',
    'record_action',
    'add_todo',
    'update_todo_status',
    'put_agent_data',
    'clear_session_state',
]
