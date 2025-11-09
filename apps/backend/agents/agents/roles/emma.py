from __future__ import annotations

from ..base import AgentContext, BaseAgent
from ...llm import get_llm_service
from ...prompts import EMMA_SYSTEM_PROMPT


class EmmaAgent(BaseAgent):
    """Product manager focusing on需求分析。"""

    def __init__(self) -> None:
        super().__init__(name='Emma', description='Product Manager')
        self._llm = get_llm_service()

    async def plan(self, context: AgentContext) -> str:
        return 'Emma 正在整理功能列表与验收标准。'

    async def act(self, context: AgentContext) -> str:
        prompt = EMMA_SYSTEM_PROMPT.format(user_message=context.user_message)
        return await self._llm.generate(prompt=prompt, provider='openai')
