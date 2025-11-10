"""Gateway-facing helper that delegates work to the agent orchestrator."""

from __future__ import annotations

from typing import Callable, Awaitable, Dict, Any, List

from agents import get_agent_orchestrator
from agents.runtime import WorkflowContext
from app.models import Message

from .session_repository import SessionRepository, session_repository
from .stream import stream_manager


class AgentRuntimeGateway:
    """Thin wrapper so FastAPI endpoints remain LLM/tool agnostic."""

    def __init__(self, store: SessionRepository) -> None:
        self._store = store
        self._orchestrator = get_agent_orchestrator()

    async def handle_user_turn(self, *, session_id: str, owner_id: str, user_id: str, user_message: str) -> List[Message]:
        """Forward a user turn to the orchestrator and persist agent replies."""
        context = WorkflowContext(session_id=session_id, user_id=user_id, user_message=user_message)
        stream_publisher = self._build_stream_publisher(session_id)
        dispatches = await self._orchestrator.handle_user_turn(context, stream_publisher=stream_publisher)
        return [
            self._store.append_message(
                session_id=session_id,
                sender=dispatch.sender,
                agent=dispatch.agent,
                content=dispatch.content,
                owner_id=owner_id,
                message_id=dispatch.message_id,
            )
            for dispatch in dispatches
        ]

    def _build_stream_publisher(self, session_id: str) -> Callable[[Dict[str, Any]], Awaitable[None]]:
        async def publish(event: Dict[str, Any]) -> None:
            await stream_manager.broadcast(session_id, event)

        return publish


# TODO: 当 agents 迁移为独立微服务时，这里改为 RPC/消息队列调用。
agent_runtime_gateway = AgentRuntimeGateway(session_repository)
