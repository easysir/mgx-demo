from __future__ import annotations

from ..base import AgentContext, AgentRunResult, BaseAgent, StreamPublisher
from ...prompts import IRIS_SYSTEM_PROMPT


class IrisAgent(BaseAgent):
    """Researcher responsible for external intelligence gathering."""

    def __init__(self) -> None:
        super().__init__(name='Iris', description='Researcher')

    async def plan(self, context: AgentContext) -> str:
        return 'Iris 正在搜索资料与外部参考。'

    async def act(
        self, context: AgentContext, stream_publisher: StreamPublisher | None = None
    ) -> AgentRunResult:
        prompt = IRIS_SYSTEM_PROMPT.format(user_message=context.user_message)
        return await self._stream_llm_response(
            context=context,
            prompt=prompt,
            provider='deepseek',
            sender='agent',
            stream_publisher=stream_publisher,
        )
