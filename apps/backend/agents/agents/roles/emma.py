from __future__ import annotations

from ..base import AgentContext, AgentRunResult, BaseAgent, StreamPublisher
from ...prompts import EMMA_SYSTEM_PROMPT


class EmmaAgent(BaseAgent):
    """Product manager focusing on需求分析。"""

    def __init__(self) -> None:
        super().__init__(name='Emma', description='Product Manager')

    async def plan(self, context: AgentContext) -> str:
        return 'Emma 正在整理功能列表与验收标准。'

    async def act(
        self, context: AgentContext, stream_publisher: StreamPublisher | None = None
    ) -> AgentRunResult:
        prompt = EMMA_SYSTEM_PROMPT.format(user_message=context.user_message)
        return await self._stream_llm_response(
            context=context,
            prompt=prompt,
            provider='deepseek',
            sender='agent',
            stream_publisher=stream_publisher,
        )
