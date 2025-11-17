"""Agent execution engine responsible for coordinating workflows.

Runs in-process for now; TODO remove tight coupling when we move to a dedicated
agent microservice communicating via RPC/queue.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Callable, Awaitable, Dict, Any, TYPE_CHECKING

from shared.types import AgentRole, SenderRole

from ..config import AgentRegistry
from ..tools import ToolExecutor
from ..context import gather_context_payload
from ..stream import StreamContext, push_stream_context, pop_stream_context

if TYPE_CHECKING:  # pragma: no cover
    from app.models import Message

@dataclass(frozen=True)
class AgentDispatch:
    sender: SenderRole
    content: str
    agent: Optional[AgentRole] = None
    message_id: Optional[str] = None


@dataclass(frozen=True)
class WorkflowContext:
    session_id: str
    user_id: str
    user_message: str
    owner_id: str
    tools: Optional[ToolExecutor] = None
    history: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


StreamPublisher = Callable[[Dict[str, Any]], Awaitable[None]]


class AgentWorkflow:
    async def generate(
        self,
        context: WorkflowContext,
        registry: AgentRegistry,
    ) -> list[AgentDispatch]:
        raise NotImplementedError


class AgentExecutor:
    def __init__(
        self,
        *,
        registry: AgentRegistry,
        workflow: AgentWorkflow,
    ) -> None:
        self._registry = registry
        self._workflow = workflow

    async def handle_user_turn(
        self,
        *,
        session_id: str,
        owner_id: str,
        user_id: str,
        user_message: str,
        tools: Optional[ToolExecutor],
        stream_publisher: Optional[StreamPublisher] = None,
        persist_fn: Callable[[SenderRole, Optional[AgentRole], str, Optional[str]], 'Message'],
    ) -> list['Message']:
        """Generate agent dispatches for a user turn."""
        payload = gather_context_payload(session_id=session_id, owner_id=owner_id)
        context = WorkflowContext(
            session_id=session_id,
            owner_id=owner_id,
            user_id=user_id,
            user_message=user_message,
            tools=tools,
            history=payload.get('history'),
            metadata=payload.get('metadata'),
        )
        stream_context = StreamContext(
            session_id=session_id,
            owner_id=owner_id,
            publisher=stream_publisher,
            persist_fn=persist_fn,
        )
        token = push_stream_context(stream_context)
        try:
            dispatches = await self._workflow.generate(context, self._registry)
        finally:
            pop_stream_context(token)
        entries = [
            (dispatch.sender, dispatch.agent, dispatch.content, dispatch.message_id)
            for dispatch in dispatches
        ]
        stream_context.record_dispatches(entries)
        return stream_context.persisted_messages()
