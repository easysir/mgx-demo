"""Event hooks that broadcast tool usage via the streaming context."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, get_args

from shared.types import AgentRole

from ..stream import publish_tool_call
from ..stream.context import current_stream_context

AGENT_NAME_SET = set(get_args(AgentRole))


async def stream_tool_call_event(tool_name: str, params: Dict[str, Any]) -> None:
    """Default hook that records a tool call as a chat message + stream event."""
    ctx = current_stream_context()
    if not ctx:
        return
    session_id = params.get('session_id')
    owner_id = params.get('owner_id')
    if not session_id or not owner_id:
        return
    raw_agent = params.get('agent')
    agent_name = raw_agent if isinstance(raw_agent, str) and raw_agent in AGENT_NAME_SET else None
    invoker = raw_agent or agent_name or 'tool'
    content = params.get('content') or f"[工具调用] {tool_name}"
    await publish_tool_call(
        tool=tool_name,
        content=content,
        invoker=str(invoker),
        agent=agent_name,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
