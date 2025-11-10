from __future__ import annotations

from ..base import AgentContext, BaseAgent
from ...llm import get_llm_service
from ...prompts import IRIS_SYSTEM_PROMPT


class IrisAgent(BaseAgent):
    """Researcher responsible for external intelligence gathering."""

    def __init__(self) -> None:
        super().__init__(name='Iris', description='Researcher')
        self._llm = get_llm_service()

    async def plan(self, context: AgentContext) -> str:
        return 'Iris 正在搜索资料与外部参考。'

    async def act(self, context: AgentContext) -> str:
        prompt = IRIS_SYSTEM_PROMPT.format(user_message=context.user_message)
        return await self._llm.generate(prompt=prompt, provider='deepseek')
