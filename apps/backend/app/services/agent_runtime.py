"""Gateway-facing helper that delegates work to the agent orchestrator and tools."""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, List

from agents import get_agent_orchestrator
from agents.runtime import WorkflowContext
from agents.tools import ToolExecutor, ToolAdapters, build_tool_executor
from app.models import Message

from .session_repository import SessionRepository, session_repository
from .stream import stream_manager
from .capabilities import sandbox_file_capability


class AgentRuntimeGateway:
    """Thin wrapper so FastAPI endpoints remain LLM/tool agnostic."""

    def __init__(self, store: SessionRepository, tools: ToolExecutor | None = None) -> None:
        # Session 仓库用于持久化消息，工具执行器负责给 Agent 暴露文件等能力
        self._store = store
        self._orchestrator = get_agent_orchestrator()
        self._tool_executor = tools or build_tool_executor(
            ToolAdapters(sandbox_file=sandbox_file_capability)
        )

    async def handle_user_turn(
        self, *, session_id: str, owner_id: str, user_id: str, user_message: str
    ) -> List[Message]:
        """Forward a user turn to the orchestrator and persist agent replies."""
        # 构造编排上下文：包含用户输入、会话身份以及可用工具
        context = WorkflowContext(
            session_id=session_id,
            user_id=user_id,
            owner_id=owner_id,
            user_message=user_message,
            tools=self._tool_executor,
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
        payload = {'session_id': session_id, 'owner_id': owner_id, **(extra_params or {})}
        return await self._tool_executor.run(tool_name, params=payload)

    def _build_stream_publisher(self, session_id: str) -> Callable[[Dict[str, Any]], Awaitable[None]]:
        # 返回闭包，供 orchestrator 在任意节点向该 session 推送事件
        async def publish(event: Dict[str, Any]) -> None:
            await stream_manager.broadcast(session_id, event)

        return publish


# TODO: 当 agents 迁移为独立微服务时，这里改为 RPC/消息队列调用。
agent_runtime_gateway = AgentRuntimeGateway(session_repository)
