"""Base class shared by all agents.

这个模块定义了 Agent 在运行时的标准接口，确保每个角色都能以一致的方式接收上下文、规划任务并输出结果。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, Optional
from uuid import uuid4

from shared.types import AgentRole, SenderRole

from ..llm import LLMProviderError, get_llm_service
from ..tools import ToolExecutor

StreamPublisher = Callable[[Dict[str, Any]], Awaitable[None]]


@dataclass(frozen=True)
class AgentRunResult:
    """标准化的 Agent 执行结果，方便 orchestrator 统一落盘。"""

    agent: AgentRole
    sender: SenderRole
    content: str
    message_id: str


@dataclass
class AgentContext:
    """Runtime context injected into each agent.

    运行时上下文会携带会话、用户和当前输入等信息，方便 Agent 在不共享状态的情况下读取所需数据。
    """

    session_id: str  # 当前对话/沙箱的唯一标识，驱动上下文隔离
    user_id: str  # 发起本轮指令的用户 ID，可用于个性化提示
    owner_id: str  # 会话实际归属者（方便共享/代办场景）
    user_message: str  # 用户本轮输入，用于生成回复或指令
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外上下文（历史摘要、配置等）
    tools: Optional[ToolExecutor] = None  # 可选工具执行器，支持文件写入等动作


class BaseAgent:
    """Base behaviour that concrete agents can extend.

    基类约定了 plan/act/report 生命周期，具体角色可按需覆写，从而保持协作流程统一。
    """

    name: AgentRole

    def __init__(self, *, name: AgentRole, description: str) -> None:
        self.name = name
        self.description = description
        self._llm = get_llm_service()

    async def plan(self, context: AgentContext) -> str:
        """Optional planning step before执行工具。"""
        raise NotImplementedError

    async def act(
        self, context: AgentContext, stream_publisher: Optional[StreamPublisher] = None
    ) -> AgentRunResult:
        """Execute核心逻辑，例如调用LLM或工具。"""
        raise NotImplementedError

    async def report(self, context: AgentContext, result: str) -> str:
        """整理输出给 Mike/用户。"""
        return result

    async def _stream_llm_response(
        self,
        *,
        context: AgentContext,
        prompt: str,
        provider: str,
        sender: SenderRole,
        stream_publisher: Optional[StreamPublisher],
        final_transform: Optional[Callable[[str], str]] = None,
    ) -> AgentRunResult:
        """统一的 LLM 流式封装，方便各角色直接调用。"""

        message_id = self._new_message_id()
        chunks: list[str] = []
        try:
            async for chunk in self._llm.stream_generate(prompt=prompt, provider=provider):
                chunks.append(chunk)
                if stream_publisher:
                    await stream_publisher(
                        {
                            'type': 'token',
                            'sender': sender,
                            'agent': self.name,
                            'content': chunk,
                            'message_id': message_id,
                            'final': False,
                        }
                    )
            full_text = ''.join(chunks)
            final_text = final_transform(full_text) if final_transform else full_text
            if stream_publisher:
                await stream_publisher(
                    {
                        'type': 'token',
                        'sender': sender,
                        'agent': self.name,
                        'content': final_text,
                        'message_id': message_id,
                        'final': True,
                    }
                )
            return AgentRunResult(agent=self.name, sender=sender, content=final_text, message_id=message_id)
        except LLMProviderError as exc:
            if stream_publisher:
                await stream_publisher(
                    {
                        'type': 'error',
                        'sender': 'status',
                        'agent': self.name,
                        'content': str(exc),
                        'message_id': message_id,
                        'final': True,
                    }
                )
            raise

    async def _emit_final_message(
        self,
        *,
        content: str,
        sender: SenderRole,
        stream_publisher: Optional[StreamPublisher],
    ) -> AgentRunResult:
        message_id = self._new_message_id()
        if stream_publisher:
            await stream_publisher(
                {
                    'type': 'token',
                    'sender': sender,
                    'agent': self.name,
                    'content': content,
                    'message_id': message_id,
                    'final': True,
                }
        )
        return AgentRunResult(agent=self.name, sender=sender, content=content, message_id=message_id)

    def _new_message_id(self) -> str:
        return str(uuid4())

    def _compose_user_message(self, context: AgentContext) -> str:
        metadata = context.metadata or {}
        sections: list[str] = []
        history = metadata.get('history')
        if history:
            sections.append(f"最近对话（供参考）:\n{history}")
        artifacts = metadata.get('artifacts')
        if artifacts:
            sections.append(f"近期文件写入（供参考）:\n{artifacts}")
        files_overview = metadata.get('files_overview') or metadata.get('files')
        if files_overview:
            sections.append(f"沙箱文件概览:\n{files_overview}")
        sections.append(f"当前用户输入:\n{context.user_message}")
        return '\n\n'.join(sections)
