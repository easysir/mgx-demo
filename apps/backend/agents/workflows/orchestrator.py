"""State-machine orchestrator describing Mike-led dynamic task routing."""

from __future__ import annotations

import json
import re
from typing import Dict, List, Optional

from shared.types import AgentRole, SenderRole

from ..config import AgentRegistry
from ..llm import LLMService
from ..prompts import SYSTEM_PROMPTS
from ..runtime.executor import AgentDispatch, AgentWorkflow, WorkflowContext

AGENT_EXECUTION_ORDER: List[AgentRole] = ['Emma', 'Bob', 'Alex', 'David', 'Iris']
AGENT_PROVIDERS: Dict[AgentRole, str] = {
    'Mike': 'openai',
    'Emma': 'openai',
    'Bob': 'anthropic',
    'Alex': 'gemini',
    'David': 'openai',
    'Iris': 'ollama',
}
FINISH_TOKENS = {'finish', '完成', '结束', 'done', 'complete'}

MIKE_PLAN_PROMPT = """\
You are Mike, the MGX team lead. Analyze the user request "{user_message}".
Available agents: {available_agents}. For the next step return JSON:
{{"next_agent": "<Emma|Bob|Alex|David|Iris|finish>", "reason": "<short text>"}}.
Explain decisions clearly in natural language before/after the JSON block."""

MIKE_REVIEW_PROMPT = """\
You are Mike. {agent_name} just reported:
\"\"\"{agent_output}\"\"\"
Based on this result, decide the next agent or finish.
Respond with JSON: {{"next_agent": "<agent|finish>", "decision": "<pass|revise|finish>", "reason": "<text>"}}."""

MIKE_SUMMARY_PROMPT = """\
You are Mike. Summarize the collaboration outcome for "{user_message}".
Include contributions from: {contributors}. Provide next recommended action."""


class SequentialWorkflow(AgentWorkflow):
    """MVP orchestrator that lets Mike动态指派或结束任务."""

    MAX_ITERATIONS = 6

    def __init__(self, llm_service: LLMService) -> None:
        self._llm_service = llm_service

    async def generate(self, context: WorkflowContext, registry: AgentRegistry) -> list[AgentDispatch]:
        dispatches: list[AgentDispatch] = []
        dispatches.append(self._status('Mike 正在评估任务，准备调度团队。'))

        available_agents = [agent for agent in AGENT_EXECUTION_ORDER if registry.is_enabled(agent)]
        visited_agents: list[AgentRole] = []
        last_agent_output: Optional[str] = None

        plan_text = await self._prompt_mike_plan(context.user_message, available_agents)
        dispatches.append(self._message('mike', 'Mike', plan_text))
        next_agent = self._extract_agent_hint(plan_text, available_agents)

        iterations = 0
        while next_agent and iterations < self.MAX_ITERATIONS:
            iterations += 1
            dispatches.append(self._status(f'Mike 将任务交给 {next_agent}。'))

            agent_output = await self._run_agent(next_agent, context.user_message)
            dispatches.append(self._message('agent', next_agent, agent_output))
            visited_agents.append(next_agent)
            last_agent_output = agent_output

            available_agents = [agent for agent in available_agents if agent != next_agent]
            review_text = await self._prompt_mike_review(context.user_message, next_agent, agent_output, available_agents)
            dispatches.append(self._message('mike', 'Mike', review_text))

            next_agent = self._extract_agent_hint(review_text, available_agents)

        dispatches.append(self._status('Mike 收齐团队结果，准备向用户汇报结论与下一步。'))
        summary = await self._prompt_mike_summary(context.user_message, visited_agents, last_agent_output)
        dispatches.append(self._message('mike', 'Mike', summary))
        return dispatches

    async def _prompt_mike_plan(self, user_message: str, available_agents: list[AgentRole]) -> str:
        prompt = MIKE_PLAN_PROMPT.format(
            user_message=user_message,
            available_agents=', '.join(available_agents) if available_agents else '暂无可用 Agent',
        )
        return await self._llm_service.generate(prompt=prompt, provider=AGENT_PROVIDERS['Mike'])

    async def _prompt_mike_review(
        self,
        user_message: str,
        agent_name: AgentRole,
        agent_output: str,
        remaining_agents: list[AgentRole],
    ) -> str:
        prompt = MIKE_REVIEW_PROMPT.format(agent_name=agent_name, agent_output=agent_output)
        if not remaining_agents:
            prompt += "\n没有剩余 Agent，可考虑 finish。"
        return await self._llm_service.generate(prompt=prompt, provider=AGENT_PROVIDERS['Mike'])

    async def _prompt_mike_summary(
        self,
        user_message: str,
        contributors: list[AgentRole],
        last_agent_output: Optional[str],
    ) -> str:
        contributor_text = ', '.join(contributors) if contributors else 'Mike'
        prompt = MIKE_SUMMARY_PROMPT.format(user_message=user_message, contributors=contributor_text)
        if last_agent_output:
            prompt += f"\n最近一次交付内容：```{last_agent_output}```"
        return await self._llm_service.generate(prompt=prompt, provider=AGENT_PROVIDERS['Mike'])

    async def _run_agent(self, agent_name: AgentRole, user_message: str) -> str:
        template = SYSTEM_PROMPTS.get(agent_name)
        prompt = template.format(user_message=user_message) if template else f'{agent_name} 正在处理 {user_message}'
        provider = AGENT_PROVIDERS.get(agent_name, 'openai')
        return await self._llm_service.generate(prompt=prompt, provider=provider)

    def _extract_agent_hint(self, text: str, candidates: list[AgentRole]) -> Optional[AgentRole]:
        if not candidates:
            if self._contains_finish_token(text):
                return None
            return None
        parsed = self._parse_json_agent(text)
        if parsed:
            normalized = self._normalize_agent(parsed)
            if normalized in candidates:
                return normalized
            if normalized is None:
                return None
        for candidate in candidates:
            if re.search(candidate, text, re.IGNORECASE):
                return candidate
        if self._contains_finish_token(text):
            return None
        return candidates[0]

    def _parse_json_agent(self, text: str) -> Optional[str]:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group())
            return data.get('next_agent') or data.get('agent')
        except json.JSONDecodeError:
            return None

    def _normalize_agent(self, agent_value: Optional[str]) -> Optional[AgentRole]:
        if not agent_value:
            return None
        value = agent_value.strip().lower()
        if value in FINISH_TOKENS:
            return None
        for agent in AGENT_EXECUTION_ORDER:
            if agent.lower() == value:
                return agent
        return None

    def _contains_finish_token(self, text: str) -> bool:
        lower = text.lower()
        return any(token in lower for token in FINISH_TOKENS)

    def _status(self, content: str) -> AgentDispatch:
        return AgentDispatch(sender='status', agent='Mike', content=content)

    def _message(self, sender: SenderRole, agent: AgentRole, content: str) -> AgentDispatch:
        return AgentDispatch(sender=sender, agent=agent, content=content)
