"""Gather workflow context data (history, files, artifacts) for agents."""

from __future__ import annotations

import logging
from typing import Dict, List, Protocol

from shared.types import AgentRole
from agents.container import file_service, FileAccessError
from .models import SessionContext
from .state import hydrate_session_context

logger = logging.getLogger(__name__)

class MessageRecord(Protocol):
    content: str
    sender: str
    agent: AgentRole | None


class SessionStore(Protocol):
    def list_messages(self, session_id: str, owner_id: str) -> List[MessageRecord]: ...


_session_store: SessionStore | None = None


def register_session_store(store: SessionStore) -> None:
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
    if not _session_store:
        return ''
    try:
        messages = _session_store.list_messages(session_id, owner_id)
    except KeyError:
        return ''
    if not messages:
        return ''
    lines: list[str] = []
    for message in messages[-limit:]:
        content = (message.content or '').strip()
        if not content or content.startswith('[工具调用]'):
            continue
        if content.startswith('[') and '写入' in content:
            continue
        sender = message.agent or message.sender
        lines.append(f"{sender}: {content}")
    return '\n'.join(lines)


def _collect_user_messages(session_id: str, owner_id: str, limit: int) -> list[str]:
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


def _collect_file_context(session_id: str, owner_id: str, limit: int) -> str:
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
        content = message.content or ''
        if '[写入' not in content and '[文件写入' not in content and '[PRD 写入' not in content:
            continue
        lines = content.splitlines()
        if not lines:
            continue
        label_line = lines[0]
        paths = [
            line.lstrip('- ').split(' (')[0].strip()
            for line in lines[1:]
            if line.strip().startswith('- ')
        ]
        for path in paths:
            if not path:
                continue
            artifacts.append(f"{label_line}: {path}")
            if len(artifacts) >= limit:
                break
    if not artifacts:
        return ''
    return '\n'.join(f"- {item}" for item in artifacts)


__all__ = ['register_session_store', 'gather_context_payload', 'build_session_context']
