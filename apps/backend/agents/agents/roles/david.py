from __future__ import annotations

from ..base import AgentContext, AgentRunResult, BaseAgent
from ..prompts import DAVID_SYSTEM_PROMPT


class DavidAgent(BaseAgent):
    """Data analyst delivering insights & 可视化建议。"""

    def __init__(self) -> None:
        super().__init__(name='David', description='Data Analyst')

    async def plan(self, context: AgentContext) -> str:
        return 'David 正在收集数据需求并设计可视化。'

    async def act(self, context: AgentContext) -> AgentRunResult:
        # TODO: remove context logging once pipeline verified
        self._format_context_for_log(context, stage='act')
        prompt = DAVID_SYSTEM_PROMPT.format(user_message=self._compose_user_message(context))
        return await self._stream_llm_response(
            context=context,
            prompt=prompt,
            provider='deepseek',
            sender='agent',
        )
