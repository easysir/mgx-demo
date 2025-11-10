from __future__ import annotations

from ..base import AgentContext, AgentRunResult, BaseAgent, StreamPublisher
from ...prompts import BOB_SYSTEM_PROMPT


class BobAgent(BaseAgent):
    """Architect in charge of技术方案。"""

    def __init__(self) -> None:
        super().__init__(name='Bob', description='Architect')

    async def plan(self, context: AgentContext) -> str:
        return 'Bob 正在评估架构与技术栈。'

    async def act(
        self, context: AgentContext, stream_publisher: StreamPublisher | None = None
    ) -> AgentRunResult:
        prompt = BOB_SYSTEM_PROMPT.format(user_message=context.user_message)
        return await self._stream_llm_response(
            context=context,
            prompt=prompt,
            provider='deepseek',
            sender='agent',
            stream_publisher=stream_publisher,
        )
