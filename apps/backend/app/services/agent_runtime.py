"""Gateway-facing helper that delegates work to the agent orchestrator and tools."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, get_args

from agents import get_agent_orchestrator
from agents.tools import ToolExecutor
from agents.tools.registry import get_tool_executor, register_event_hook
from agents.container.capabilities import sandbox_file_capability
from agents.context import register_session_store
from agents.stream import file_change_event, tool_call_event
from app.models import Message
from shared.types import AgentRole, SenderRole

from .session_repository import SessionRepository, session_repository
from .stream import stream_manager

logger = logging.getLogger(__name__)
AGENT_NAME_SET = set(get_args(AgentRole))


class AgentRuntimeGateway:
    """Thin wrapper so FastAPI endpoints remain LLM/tool agnostic."""

    def __init__(self, store: SessionRepository, tools: ToolExecutor | None = None) -> None:
        # Session 仓库用于持久化消息，工具执行器负责给 Agent 暴露文件等能力
        self._store = store
        self._tool_executor = tools or get_tool_executor()
        register_event_hook(self._handle_tool_call_event)
        sandbox_file_capability.set_file_change_hook(self._handle_file_change_event)
        register_session_store(self._store)
        self._orchestrator = get_agent_orchestrator()

    async def handle_user_turn(
        self, *, session_id: str, owner_id: str, user_id: str, user_message: str
    ) -> List[Message]:
        """Forward a user turn to the orchestrator and persist agent replies."""
        # 为该 session 生成 WebSocket 推送器，编排器在生成 token/status 时复用
        stream_publisher = self._build_stream_publisher(session_id)
        # 交给 orchestrator 运行 Mike 状态机，StreamContext 内部会记录落库顺序
        persist_fn = self._build_persist_fn(session_id, owner_id)
        messages = await self._orchestrator.handle_user_turn(
            session_id=session_id,
            owner_id=owner_id,
            user_id=user_id,
            user_message=user_message,
            tools=self._tool_executor,
            stream_publisher=stream_publisher,
            persist_fn=persist_fn,
        )
        return messages

    async def execute_tool(
        self,
        tool_name: str,
        *,
        session_id: str,
        owner_id: str,
        extra_params: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Execute a registered tool on behalf of an agent or API consumer."""
        # 标准化工具调用入参，附带 session/owner 以做沙箱隔离
        payload: Dict[str, Any] = {'session_id': session_id, 'owner_id': owner_id}
        if extra_params:
            payload.update(extra_params)
        payload.setdefault('agent', (extra_params or {}).get('agent', 'external'))
        return await self._tool_executor.run(tool_name, params=payload)

    def _build_stream_publisher(self, session_id: str) -> Callable[[Dict[str, Any]], Awaitable[None]]:
        # 返回闭包，供 orchestrator 在任意节点向该 session 推送事件
        async def publish(event: Dict[str, Any]) -> None:
            await stream_manager.broadcast(session_id, event)

        return publish

    def _build_persist_fn(
        self, session_id: str, owner_id: str
    ) -> Callable[[SenderRole, Optional[AgentRole], str, Optional[str], Optional[datetime]], Message]:
        def persist(
            sender: SenderRole,
            agent: Optional[AgentRole],
            content: str,
            message_id: Optional[str],
            timestamp: Optional[datetime],
        ) -> Message:
            return self._store.append_message(
                session_id=session_id,
                sender=sender,
                agent=agent,
                content=content,
                owner_id=owner_id,
                message_id=message_id,
                timestamp=timestamp,
            )

        return persist

    async def _handle_tool_call_event(self, tool_name: str, params: Dict[str, Any]) -> None:
        session_id = params.get('session_id')
        owner_id = params.get('owner_id')
        if not session_id or not owner_id:
            logger.debug('忽略缺少 session/owner 的工具调用记录: %s', tool_name)
            return
        raw_agent = params.get('agent')
        agent_name = raw_agent if isinstance(raw_agent, str) and raw_agent in AGENT_NAME_SET else None
        invoker = raw_agent or agent_name or 'tool'
        content = f"[工具调用] {tool_name}"
        message = self._store.append_message(
            session_id=session_id,
            sender='agent',
            agent=agent_name,
            content=content,
            owner_id=owner_id,
        )
        event_payload = tool_call_event(
            tool=tool_name,
            content=content,
            invoker=invoker,
            agent=agent_name,
            message_id=message.id,
            timestamp=message.timestamp.replace(tzinfo=timezone.utc).isoformat(),
        )
        try:
            await stream_manager.broadcast(session_id, event_payload)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning('Failed to broadcast tool event for %s: %s', session_id, exc)

    async def _handle_file_change_event(self, session_id: str, payload: Dict[str, Any]) -> None:
        try:
            await stream_manager.broadcast(session_id, payload)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning('Failed to broadcast file change for %s: %s', session_id, exc)



# TODO: 当 agents 迁移为独立微服务时，这里改为 RPC/消息队列调用。
agent_runtime_gateway = AgentRuntimeGateway(session_repository)
