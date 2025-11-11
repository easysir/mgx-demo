from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional, Tuple

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
        prompt = MIKE_SYSTEM_PROMPT.format(user_message=self._compose_user_message(context))
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
        if available_agents:
            available_text = '\n'.join(f"- {entry}" for entry in available_agents)
        else:
            available_text = '暂无可用 Agent'
        prompt = MIKE_PLAN_PROMPT.format(
            user_message=self._compose_user_message(context),
            available_agents=available_text,
        )
        return await self._stream_llm_response(
            context=context,
            prompt=prompt,
            provider='deepseek',
            sender='mike',
            stream_publisher=stream_publisher,
            final_transform=self._format_plan_response,
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
            final_transform=lambda text: self._format_review_response(text, agent_name),
        )

    async def summarize_team(
        self,
        context: AgentContext,
        contributions: list[Tuple[str, str]],
        stream_publisher: StreamPublisher | None = None,
    ) -> AgentRunResult:
        contributions_text = self._render_contributions(contributions)
        prompt = MIKE_SUMMARY_PROMPT.format(
            user_message=self._compose_user_message(context),
            contributions=contributions_text,
        )
        return await self._stream_llm_response(
            context=context,
            prompt=prompt,
            provider='deepseek',
            sender='mike',
            stream_publisher=stream_publisher,
            final_transform=lambda text: self._format_summary_response(text, context.user_message),
        )

    def _format_plan_response(self, raw: str) -> str:
        data = self._extract_json_block(raw)
        if not data:
            return raw.strip()
        next_agent = data.get('next_agent')
        reason = data.get('reason')
        lines = ["## Mike 任务规划"]
        if next_agent:
            lines.append(f"- 下一位 Agent：{next_agent}")
        if reason:
            lines.append(f"- 决策理由：{reason}")
        return "\n".join(lines).strip()

    def _format_review_response(self, raw: str, agent_name: str) -> str:
        data = self._extract_json_block(raw)
        if not data:
            return raw.strip()
        decision = data.get('decision')
        next_agent = data.get('next_agent')
        reason = data.get('reason')
        lines = [f"## Mike 复盘 {agent_name}"]
        if decision:
            lines.append(f"- 决策：{decision}")
        if next_agent:
            lines.append(f"- 下一步：{next_agent}")
        if reason:
            lines.append(f"- 说明：{reason}")
        return "\n".join(lines).strip()

    def _format_summary_response(self, raw: str, user_message: str) -> str:
        summary_body = raw.strip()
        lines = [
            '## Mike 最终汇报',
            f"**用户需求概述**：{user_message.strip()}",
            '',
            summary_body,
            '',
            '如需进一步修改或新增功能，随时告诉我，我会继续调度团队。'
        ]
        return '\n'.join(line for line in lines if line.strip())

    def _render_contributions(self, contributions: list[Tuple[str, str]]) -> str:
        if not contributions:
            return '- 暂无额外贡献（只有 Mike）'
        items = []
        for agent, output in contributions:
            snippet = output.strip()
            if len(snippet) > 400:
                snippet = snippet[:400] + '...'
            items.append(f"- {agent}: {snippet}")
        return '\n'.join(items)

    def _extract_json_block(self, text: str) -> Dict[str, Any] | None:
        match = re.search(r'\{.*?\}', text, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group())
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            return None
        return None
