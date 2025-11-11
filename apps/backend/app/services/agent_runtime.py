"""Gateway-facing helper that delegates work to the agent orchestrator and tools."""

from __future__ import annotations

import json
import logging
from datetime import timezone
from typing import Any, Awaitable, Callable, Dict, List, get_args

from agents import get_agent_orchestrator
from agents.runtime import WorkflowContext
from agents.tools import ToolExecutor, ToolAdapters, build_tool_executor
from app.models import Message
from shared.types import AgentRole

from .session_repository import SessionRepository, session_repository
from .stream import stream_manager
from .capabilities import sandbox_file_capability

logger = logging.getLogger(__name__)
AGENT_NAME_SET = set(get_args(AgentRole))


class AgentRuntimeGateway:
    """Thin wrapper so FastAPI endpoints remain LLM/tool agnostic."""

    def __init__(self, store: SessionRepository, tools: ToolExecutor | None = None) -> None:
        # Session 仓库用于持久化消息，工具执行器负责给 Agent 暴露文件等能力
        self._store = store
        self._orchestrator = get_agent_orchestrator()
        self._tool_executor = tools or build_tool_executor(
            ToolAdapters(sandbox_file=sandbox_file_capability)
        )
        self._tool_executor.set_event_hook(self._handle_tool_call_event)

    async def handle_user_turn(
        self, *, session_id: str, owner_id: str, user_id: str, user_message: str
    ) -> List[Message]:
        """Forward a user turn to the orchestrator and persist agent replies."""
        # 构造编排上下文：包含用户输入、会话身份以及可用工具
        history_text = self._collect_history(session_id=session_id, owner_id=owner_id)
        context = WorkflowContext(
            session_id=session_id,
            user_id=user_id,
            owner_id=owner_id,
            user_message=user_message,
            tools=self._tool_executor,
            history=history_text,
        )
        # 为该 session 生成 WebSocket 推送器，编排器在生成 token/status 时复用
        stream_publisher = self._build_stream_publisher(session_id)
        # 交给 orchestrator 运行 Mike 状态机，拿到各 Agent 的 dispatch 结果
        dispatches = await self._orchestrator.handle_user_turn(context, stream_publisher=stream_publisher)
        # 将所有 Agent 输出回写 SessionStore，确保 REST 与回放一致
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

    def _collect_history(self, *, session_id: str, owner_id: str, limit: int = 8) -> str:
        try:
            messages = self._store.list_messages(session_id, owner_id)
        except KeyError:
            return ''
        if not messages:
            return ''
        recent = messages[-limit:]
        lines = []
        for message in recent:
            sender = message.agent or message.sender
            lines.append(f"{sender}: {message.content}")
        return '\n'.join(lines)

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
        event_payload = {
            'type': 'tool_call',
            'sender': 'agent',
            'agent': agent_name,
            'invoker': invoker,
            'tool': tool_name,
            'content': content,
            'message_id': message.id,
            'final': True,
            'timestamp': message.timestamp.replace(tzinfo=timezone.utc).isoformat(),
        }
        try:
            await stream_manager.broadcast(session_id, event_payload)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning('Failed to broadcast tool event for %s: %s', session_id, exc)



# TODO: 当 agents 迁移为独立微服务时，这里改为 RPC/消息队列调用。
agent_runtime_gateway = AgentRuntimeGateway(session_repository)
