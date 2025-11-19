"""Structured context models shared across agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from shared.types import AgentRole


@dataclass
class ActionLogEntry:
    """Represents a key action performed by an agent in recent turns."""

    agent: AgentRole
    action: str
    result: str
    status: str = 'success'
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TodoEntry:
    """Tracks important pending items surfaced during the workflow."""

    description: str
    owner: str
    priority: str = 'medium'
    status: str = 'pending'
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentContextView:
    """Per-agent projection of the current session context."""

    session_id: str
    owner_id: str
    user_id: str
    user_messages: List[str]
    most_recent_user_message: str
    system_prompt: Optional[str]
    history: str
    artifacts: str
    files_overview: str
    action_log: List[ActionLogEntry]
    pending_todos: List[TodoEntry]
    agent_data: Dict[str, Any]


@dataclass
class SessionContext:
    """Global structured context that can spawn per-agent projections."""

    session_id: str
    owner_id: str
    user_id: str
    user_message: List[str] = field(default_factory=list)
    most_recent_user_message: str = ''
    conversation_history: str = ''
    artifacts: str = ''
    files_overview: str = ''
    action_log: List[ActionLogEntry] = field(default_factory=list)
    pending_todos: List[TodoEntry] = field(default_factory=list)
    agent_specific: Dict[AgentRole, Dict[str, Any]] = field(default_factory=dict)

    def for_agent(
        self,
        agent: AgentRole,
        *,
        system_prompt: Optional[str] = None,
        extras: Optional[Dict[str, Any]] = None,
    ) -> AgentContextView:
        payload = dict(self.agent_specific.get(agent, {}))
        if extras:
            payload.update(extras)
        return AgentContextView(
            session_id=self.session_id,
            owner_id=self.owner_id,
            user_id=self.user_id,
            user_messages=list(self.user_message),
            most_recent_user_message=self.most_recent_user_message,
            system_prompt=system_prompt,
            history=self.conversation_history,
            artifacts=self.artifacts,
            files_overview=self.files_overview,
            action_log=list(self.action_log),
            pending_todos=list(self.pending_todos),
            agent_data=payload,
        )

    def to_metadata_payload(self) -> Dict[str, str]:
        """Legacy helper so existing metadata consumers can degrade gracefully."""

        metadata: Dict[str, str] = {}
        if self.files_overview:
            metadata['files_overview'] = self.files_overview
        if self.artifacts:
            metadata['artifacts'] = self.artifacts
        if self.conversation_history:
            metadata['history'] = self.conversation_history
        if self.action_log:
            rendered = '\n'.join(
                f"- [{entry.status}] {entry.agent} {entry.action}: {entry.result}"
                for entry in self.action_log
            )
            metadata['action_log'] = rendered
        if self.pending_todos:
            todo_lines = '\n'.join(
                f"- ({todo.priority}) {todo.description} [{todo.status}]"
                for todo in self.pending_todos
            )
            metadata['pending_todos'] = todo_lines
        return metadata


__all__ = ['ActionLogEntry', 'TodoEntry', 'SessionContext', 'AgentContextView']
