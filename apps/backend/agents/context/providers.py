"""Gather workflow context data (history, files, artifacts) for agents."""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Protocol, Optional

from shared.types import AgentRole
from agents.container import file_service, FileAccessError
from ..agents.base import AgentContext
from ..tools import ToolExecutor
from .models import SessionContext
from .state import hydrate_session_context, get_session_state

logger = logging.getLogger(__name__)

class MessageRecord(Protocol):
    content: str
    sender: str
    agent: AgentRole | None


class SessionStore(Protocol):
    def list_messages(self, session_id: str, owner_id: str) -> List[MessageRecord]: ...


_session_store: SessionStore | None = None


def register_session_store(store: SessionStore) -> None:
    """注册会话消息存取实现，统一由 Context 层拉取原始消息。"""
    global _session_store
    _session_store = store


def build_session_context(
    *,
    session_id: str,
    owner_id: str,
    user_id: str,
    user_message: str,
    history_limit: int = 8,
    file_limit: int = 6,
    artifact_limit: int = 5,
) -> SessionContext:
    # 分别采集 history/files/artifacts，再拼装为结构化 SessionContext
    history = _collect_history(session_id, owner_id, history_limit)  # 拉取最近的会话消息用作上下文
    files = _collect_file_context(session_id, owner_id, file_limit)  # 同步沙箱内的文件片段
    artifacts = _collect_recent_artifacts(session_id, owner_id, artifact_limit)  # 汇总任务产出的代码/结果
    user_messages = _collect_user_messages(session_id, owner_id, history_limit)
    trimmed_input = (user_message or '').strip()
    if trimmed_input:
        user_messages = (user_messages + [trimmed_input])[-history_limit:]
    most_recent_user_message = trimmed_input or (user_messages[-1] if user_messages else '')
    return hydrate_session_context(
        session_id=session_id,
        owner_id=owner_id,
        user_id=user_id,
        user_messages=user_messages,
        most_recent_user_message=most_recent_user_message,
        history=history,
        artifacts=artifacts,
        files_overview=files,
    )


def build_agent_context_view(
    *,
    session_id: str,
    owner_id: str,
    user_id: str,
    user_message: str,
    tools: Optional[ToolExecutor] = None,
    session_context: Optional[SessionContext] = None,
) -> AgentContext:
    # 将 SessionContext 中的结构化数据投影到 AgentContext，供各角色读取
    metadata: Dict[str, Any] = {}
    history = ''
    artifacts = ''
    files_overview = ''
    action_log = []
    pending = []
    agent_specific: Dict[AgentRole, Dict[str, Any]] = {}
    if session_context:
        metadata.update(session_context.to_metadata_payload())
        history = session_context.conversation_history
        artifacts = session_context.artifacts
        files_overview = session_context.files_overview
        action_log = session_context.action_log
        pending = session_context.pending_todos
        agent_specific = session_context.agent_specific
    return AgentContext(
        session_id=session_id,
        user_id=user_id,
        owner_id=owner_id,
        user_message=user_message,
        metadata=metadata,
        tools=tools,
        history=history,
        artifacts=artifacts,
        files_overview=files_overview,
        action_log=action_log,
        pending_todos=pending,
        agent_data={},
        agent_specific=agent_specific,
    )

def gather_context_payload(
    *,
    session_id: str,
    owner_id: str,
    user_id: str = '',
    user_message: str = '',
    history_limit: int = 8,
    file_limit: int = 6,
    artifact_limit: int = 5,
) -> Dict[str, str | Dict[str, str] | None]:
    # 兼容旧接口：返回历史文本 + metadata，供流式渲染或日志
    session_context = build_session_context(
        session_id=session_id,
        owner_id=owner_id,
        user_id=user_id,
        user_message=user_message,
        history_limit=history_limit,
        file_limit=file_limit,
        artifact_limit=artifact_limit,
    )
    metadata = session_context.to_metadata_payload()
    logger.info(
        'Context payload assembled: history=%s files=%s artifacts=%s metadata=%s',
        session_context.conversation_history,
        session_context.files_overview,
        session_context.artifacts,
        metadata,
    )
    return {
        'history': session_context.conversation_history or None,
        'metadata': metadata or None,
    }


def _collect_history(session_id: str, owner_id: str, limit: int) -> str:
    # 优先返回动作时间线（精简版上下文）
    timeline = _collect_action_timeline(session_id, limit)
    return timeline


def _collect_action_timeline(session_id: str, limit: int) -> str:
    # 从持久化状态中提取 action_log，以“步骤”形式展现
    state = get_session_state(session_id)
    if not state.action_log:
        return ''
    entries = state.action_log[-limit:]
    lines: list[str] = []
    for entry in entries:
        metadata = entry.metadata or {}
        summary = metadata.get('summary_line') or _compress_text(entry.result)
        step_id = metadata.get('step_id')
        prefix = f"步骤 {step_id}" if step_id else f"步骤 {len(lines) + 1}"
        detail_hint = f"（详情：{metadata.get('detail_path')}）" if metadata.get('detail_path') else ''
        lines.append(f"{prefix} · {entry.agent}: {summary}{detail_hint}")
    return '\n'.join(lines)


def _collect_user_messages(session_id: str, owner_id: str, limit: int) -> list[str]:
    # 收集最近 N 条用户消息，给 Prompt 生成器使用
    if not _session_store:
        return []
    try:
        messages = _session_store.list_messages(session_id, owner_id)
    except KeyError:
        return []
    user_lines: list[str] = []
    for message in messages:
        if getattr(message, 'sender', '') != 'user':
            continue
        content = (message.content or '').strip()
        if not content:
            continue
        user_lines.append(content)
    if limit and limit > 0:
        user_lines = user_lines[-limit:]
    return user_lines


def _compress_text(text: str, max_len: int = 160) -> str:
    cleaned = (text or '').strip()
    if not cleaned:
        return '无输出'
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned[: max_len - 3] + '...' if len(cleaned) > max_len else cleaned


def _collect_file_context(session_id: str, owner_id: str, limit: int) -> str:
    # 通过文件服务扫描沙箱目录，粗略给出文件结构概览
    try:
        entries = file_service.list_tree(
            session_id=session_id,
            owner_id=owner_id,
            root='',
            depth=4,
            include_hidden=False,
        )
    except FileAccessError:
        return ''
    except Exception:
        return ''
    files: list[str] = []

    def visit(nodes: list[dict]) -> None:
        for node in nodes:
            if len(files) >= limit:
                return
            path = node.get('path') or node.get('name', '')
            if node.get('type') == 'file':
                files.append(f"{path} (size {node.get('size', 0)})")
            children = node.get('children')
            if children:
                visit(children)

    visit(entries)
    if not files:
        return ''
    return '\n'.join(f"- {item}" for item in files)


def _collect_recent_artifacts(session_id: str, owner_id: str, limit: int) -> str:
    # 从工具消息中提取“写入”记录，生成最近文件写入摘要
    if not _session_store:
        return ''
    try:
        messages = _session_store.list_messages(session_id, owner_id)
    except KeyError:
        return ''
    artifacts: list[str] = []
    for message in reversed(messages):
        if len(artifacts) >= limit:
            break
        entries = _extract_artifact_entries(message.content or '')
        if not entries:
            continue
        for entry in entries:
            artifacts.append(entry)
            if len(artifacts) >= limit:
                break
    if not artifacts:
        return ''
    return '\n'.join(f"- {item}" for item in artifacts)


def _extract_artifact_entries(content: str) -> list[str]:
    entries: list[str] = []
    current_label: str | None = None
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('['):
            current_label = stripped if '写入' in stripped else None
            continue
        if not current_label:
            continue
        if not stripped.startswith('-'):
            current_label = None
            continue
        candidate = _normalize_artifact_line(stripped.lstrip('-').strip())
        if not candidate:
            continue
        entries.append(f"{current_label}: {candidate}")
    return entries


def _normalize_artifact_line(text: str) -> str | None:
    if not text:
        return None
    target = text
    if ': ' in text:
        _, maybe_path = text.split(': ', 1)
        maybe_path = maybe_path.strip()
        if _looks_like_path(maybe_path):
            target = maybe_path
        elif not _looks_like_path(target):
            return None
    if not _looks_like_path(target):
        return None
    target = target.split(' (')[0].strip()
    return target or None


def _looks_like_path(value: str) -> bool:
    if '/' in value:
        return True
    lowered = value.lower()
    return lowered.endswith((
        '.py', '.ts', '.tsx', '.js', '.jsx', '.json', '.md', '.txt',
        '.yml', '.yaml', '.toml', '.lock', '.cfg', '.ini', '.css',
        '.scss', '.html', '.rs', '.go', '.java', '.kt', '.sh',
    ))


__all__ = ['register_session_store', 'gather_context_payload', 'build_session_context', 'build_agent_context_view']
