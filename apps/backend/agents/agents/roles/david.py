from __future__ import annotations

from ..base import AgentContext, BaseAgent
from ...llm import get_llm_service
from ...prompts import DAVID_SYSTEM_PROMPT


class DavidAgent(BaseAgent):
    """Data analyst delivering insights & 可视化建议。"""

    def __init__(self) -> None:
        super().__init__(name='David', description='Data Analyst')
        self._llm = get_llm_service()

    async def plan(self, context: AgentContext) -> str:
        return 'David 正在收集数据需求并设计可视化。'

    async def act(self, context: AgentContext) -> str:
        prompt = DAVID_SYSTEM_PROMPT.format(user_message=context.user_message)
        return await self._llm.generate(prompt=prompt, provider='deepseek')
