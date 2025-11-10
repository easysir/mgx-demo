from __future__ import annotations

from ..base import AgentContext, BaseAgent
from ...llm import get_llm_service
from ...prompts import BOB_SYSTEM_PROMPT


class BobAgent(BaseAgent):
    """Architect in charge of技术方案。"""

    def __init__(self) -> None:
        super().__init__(name='Bob', description='Architect')
        self._llm = get_llm_service()

    async def plan(self, context: AgentContext) -> str:
        return 'Bob 正在评估架构与技术栈。'

    async def act(self, context: AgentContext) -> str:
        prompt = BOB_SYSTEM_PROMPT.format(user_message=context.user_message)
        return await self._llm.generate(prompt=prompt, provider='deepseek')
