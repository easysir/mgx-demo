"""Agent execution engine responsible for coordinating workflows.

Runs in-process for now; TODO remove tight coupling when we move to a dedicated
agent microservice communicating via RPC/queue.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Callable, Awaitable, Dict, Any

from shared.types import AgentRole, SenderRole

from ..config import AgentRegistry


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


StreamPublisher = Callable[[Dict[str, Any]], Awaitable[None]]


class AgentWorkflow:
    async def generate(
        self,
        context: WorkflowContext,
        registry: AgentRegistry,
        stream_publisher: Optional[StreamPublisher] = None,
    ) -> list[AgentDispatch]:
        raise NotImplementedError


class AgentExecutor:
    def __init__(self, *, registry: AgentRegistry, workflow: AgentWorkflow) -> None:
        self._registry = registry
        self._workflow = workflow

    async def handle_user_turn(
        self, context: WorkflowContext, stream_publisher: Optional[StreamPublisher] = None
    ) -> list[AgentDispatch]:
        """Generate agent dispatches for a user turn."""
        return await self._workflow.generate(context, self._registry, stream_publisher=stream_publisher)
