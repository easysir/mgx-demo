"""Agent execution engine responsible for coordinating workflows.

Runs in-process for now; TODO remove tight coupling when we move to a dedicated
agent microservice communicating via RPC/queue.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Callable, Awaitable, Dict, Any, TYPE_CHECKING

from shared.types import AgentRole, SenderRole

from ..config import AgentRegistry
from ..tools import ToolExecutor
from ..context import build_session_context
from ..context.models import SessionContext
from ..stream import StreamContext, push_stream_context, pop_stream_context

if TYPE_CHECKING:  # pragma: no cover
    from app.models import Message

@dataclass(frozen=True)
class WorkflowContext:
    session_id: str
    user_id: str
    user_message: str
    owner_id: str
    tools: Optional[ToolExecutor] = None
    session_context: Optional[SessionContext] = None


StreamPublisher = Callable[[Dict[str, Any]], Awaitable[None]]


class AgentWorkflow:
    async def generate(
        self,
        context: WorkflowContext,
        registry: AgentRegistry,
    ) -> None:
        raise NotImplementedError


class AgentExecutor:
    def __init__(
        self,
        *,
        registry: AgentRegistry,
        workflow: AgentWorkflow,
        tool_executor: ToolExecutor,
    ) -> None:
        self._registry = registry
        self._workflow = workflow
        self._tool_executor = tool_executor

    async def handle_user_turn(
        self,
        *,
        session_id: str,
        owner_id: str,
        user_id: str,
        user_message: str,
        stream_publisher: Optional[StreamPublisher] = None,
        persist_fn: Callable[[SenderRole, Optional[AgentRole], str, Optional[str], Optional[datetime]], 'Message'],
        ) -> list['Message']:
        """Run the workflow for a user turn and return persisted messages."""
        session_context = build_session_context(
            session_id=session_id,
            owner_id=owner_id,
            user_id=user_id,
            user_message=user_message,
        )
        workflow_context = WorkflowContext(
            session_id=session_id,
            owner_id=owner_id,
            user_id=user_id,
            user_message=user_message,
            tools=self._tool_executor,
            session_context=session_context,
        )
        stream_context = StreamContext(
            session_id=session_id,
            owner_id=owner_id,
            publisher=stream_publisher,
            persist_fn=persist_fn,
        )
        token = push_stream_context(stream_context)
        try:
            await self._workflow.generate(workflow_context, self._registry)
        finally:
            pop_stream_context(token)
        return stream_context.persisted_messages()
