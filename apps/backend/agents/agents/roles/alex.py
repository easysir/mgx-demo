from __future__ import annotations

from ..base import AgentContext, BaseAgent
from ...llm import get_llm_service
from ...prompts import ALEX_SYSTEM_PROMPT


class AlexAgent(BaseAgent):
    """Engineer responsible for实现与部署。"""

    def __init__(self) -> None:
        super().__init__(name='Alex', description='Engineer')
        self._llm = get_llm_service()

    async def plan(self, context: AgentContext) -> str:
        return 'Alex 正在拆解开发任务与工具调用顺序。'

    async def act(self, context: AgentContext) -> str:
        prompt = ALEX_SYSTEM_PROMPT.format(user_message=context.user_message)
        return await self._llm.generate(prompt=prompt, provider='gemini')
