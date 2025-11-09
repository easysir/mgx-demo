from __future__ import annotations

from ..base import AgentContext, BaseAgent
from ...llm import get_llm_service
from ...prompts import MIKE_SYSTEM_PROMPT


class MikeAgent(BaseAgent):
    """Team lead responsible for规划与质量把关。"""

    def __init__(self) -> None:
        super().__init__(name='Mike', description='Team Lead / Planner')
        self._llm = get_llm_service()

    async def plan(self, context: AgentContext) -> str:
        return f'Mike 正在审阅需求“{context.user_message}”，准备拆解任务。'

    async def act(self, context: AgentContext) -> str:
        prompt = MIKE_SYSTEM_PROMPT.format(user_message=context.user_message)
        return await self._llm.generate(prompt=prompt, provider='openai')
