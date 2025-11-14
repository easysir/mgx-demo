"""Gather workflow context data (history, files, artifacts) for agents."""

from __future__ import annotations

from typing import Dict, List, Protocol

from shared.types import AgentRole
from agents.container import file_service, FileAccessError


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


def gather_context_payload(
    *,
    session_id: str,
    owner_id: str,
    history_limit: int = 8,
    file_limit: int = 6,
    artifact_limit: int = 5,
) -> Dict[str, str | Dict[str, str] | None]:
    history = _collect_history(session_id, owner_id, history_limit)
    files = _collect_file_context(session_id, owner_id, file_limit)
    artifacts = _collect_recent_artifacts(session_id, owner_id, artifact_limit)
    metadata: Dict[str, str] = {}
    if files:
        metadata['files_overview'] = files
    if artifacts:
        metadata['artifacts'] = artifacts
    return {
        'history': history or None,
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


def _collect_file_context(session_id: str, owner_id: str, limit: int) -> str:
    try:
        entries = file_service.list_tree(
            session_id=session_id,
            owner_id=owner_id,
            root='',
            depth=2,
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


__all__ = ['register_session_store', 'gather_context_payload']
