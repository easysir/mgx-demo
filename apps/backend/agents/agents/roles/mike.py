from __future__ import annotations

from ..base import AgentContext, AgentRunResult, BaseAgent, StreamPublisher
from ...prompts import MIKE_PLAN_PROMPT, MIKE_REVIEW_PROMPT, MIKE_SUMMARY_PROMPT, MIKE_SYSTEM_PROMPT


class MikeAgent(BaseAgent):
    """Team lead responsible for规划与质量把关。"""

    def __init__(self) -> None:
        super().__init__(name='Mike', description='Team Lead / Planner')

    async def plan(self, context: AgentContext) -> str:
        return f'Mike 正在审阅需求“{context.user_message}”，准备拆解任务。'

    async def act(
        self, context: AgentContext, stream_publisher: StreamPublisher | None = None
    ) -> AgentRunResult:
        prompt = MIKE_SYSTEM_PROMPT.format(user_message=context.user_message)
        return await self._stream_llm_response(
            context=context,
            prompt=prompt,
            provider='deepseek',
            sender='mike',
            stream_publisher=stream_publisher,
        )

    async def plan_next_agent(
        self,
        context: AgentContext,
        available_agents: list[str],
        stream_publisher: StreamPublisher | None = None,
    ) -> AgentRunResult:
        prompt = MIKE_PLAN_PROMPT.format(
            user_message=context.user_message,
            available_agents=', '.join(available_agents) if available_agents else '暂无可用 Agent',
        )
        return await self._stream_llm_response(
            context=context,
            prompt=prompt,
            provider='deepseek',
            sender='mike',
            stream_publisher=stream_publisher,
        )

    async def review_agent_output(
        self,
        context: AgentContext,
        agent_name: str,
        agent_output: str,
        remaining_agents: list[str],
        stream_publisher: StreamPublisher | None = None,
    ) -> AgentRunResult:
        prompt = MIKE_REVIEW_PROMPT.format(agent_name=agent_name, agent_output=agent_output)
        if not remaining_agents:
            prompt += "\n没有剩余 Agent，可考虑 finish。"
        return await self._stream_llm_response(
            context=context,
            prompt=prompt,
            provider='deepseek',
            sender='mike',
            stream_publisher=stream_publisher,
        )

    async def summarize_team(
        self,
        context: AgentContext,
        contributors: list[str],
        last_agent_output: str | None,
        stream_publisher: StreamPublisher | None = None,
    ) -> AgentRunResult:
        contributor_text = ', '.join(contributors) if contributors else 'Mike'
        prompt = MIKE_SUMMARY_PROMPT.format(user_message=context.user_message, contributors=contributor_text)
        if last_agent_output:
            prompt += f"\n最近一次交付内容：```{last_agent_output}```"
        return await self._stream_llm_response(
            context=context,
            prompt=prompt,
            provider='deepseek',
            sender='mike',
            stream_publisher=stream_publisher,
        )
