"""State-machine orchestrator describing Mike-led dynamic task routing with streaming."""

from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from shared.types import AgentRole

from ..config import AgentRegistry
from ..runtime.executor import AgentDispatch, AgentWorkflow, WorkflowContext
from ..agents.base import AgentContext, AgentRunResult
from ..agents.roles.alex import AlexAgent
from ..agents.roles.bob import BobAgent
from ..agents.roles.david import DavidAgent
from ..agents.roles.emma import EmmaAgent
from ..agents.roles.iris import IrisAgent
from ..agents.roles.mike import MikeAgent
from ..stream import publish_status

AGENT_EXECUTION_ORDER: List[AgentRole] = ['Emma', 'Bob', 'Alex', 'David', 'Iris']
FINISH_TOKENS = {'finish', '完成', '结束', 'done', 'complete'}


class SequentialWorkflow(AgentWorkflow):
    """MVP orchestrator that让 Mike 负责编排，具体执行交给各角色 Agent。"""

    MAX_ITERATIONS = 6

    def __init__(self) -> None:
        self._mike_agent = MikeAgent()
        self._agent_pool: Dict[AgentRole, object] = {
            'Emma': EmmaAgent(),
            'Bob': BobAgent(),
            'Alex': AlexAgent(),
            'David': DavidAgent(),
            'Iris': IrisAgent(),
        }

    async def generate(
        self,
        context: WorkflowContext,
        registry: AgentRegistry,
    ) -> list[AgentDispatch]:
        dispatches: list[AgentDispatch] = []
        available_agents = [agent for agent in AGENT_EXECUTION_ORDER if registry.is_enabled(agent)]
        available_agents_descriptions = registry.describe_agents(available_agents)
        agent_context = self._build_agent_context(context)
        agent_contributions: list[Tuple[AgentRole, str]] = []

        await self._emit_status(
            dispatches,
            context.session_id,
            'Mike 正在评估任务，准备调度团队。',
        )

        plan_result = await self._mike_agent.plan_next_agent(agent_context, available_agents_descriptions)
        dispatches.append(self._dispatch_from_result(plan_result))
        next_agent = self._extract_agent_hint(plan_result.content, available_agents)

        iterations = 0
        
        while next_agent and iterations < self.MAX_ITERATIONS:
            iterations += 1
            await self._emit_status(
                dispatches,
                context.session_id,
                f'Mike 将任务交给 {next_agent}。',
            )

            agent_result = await self._run_agent(next_agent, agent_context)
            dispatches.append(self._dispatch_from_result(agent_result))
            agent_contributions.append((next_agent, agent_result.content))

            available_agents = [agent for agent in available_agents if agent != next_agent]
            review_result = await self._mike_agent.review_agent_output(
                agent_context,
                next_agent,
                agent_result.content,
                available_agents,
            )
            dispatches.append(self._dispatch_from_result(review_result))

            next_agent = self._extract_agent_hint(review_result.content, available_agents)

        await self._emit_status(
            dispatches,
            context.session_id,
            'Mike 收齐团队结果，准备向用户汇报结论与下一步。',
        )
        summary_result = await self._mike_agent.summarize_team(
            agent_context,
            agent_contributions,
        )
        dispatches.append(self._dispatch_from_result(summary_result))
        return dispatches

    def _build_agent_context(self, context: WorkflowContext) -> AgentContext:
        metadata: Dict[str, Any] = {}
        if context.history:
            metadata['history'] = context.history
        if context.metadata:
            metadata.update(context.metadata)
        return AgentContext(
            session_id=context.session_id,
            user_id=context.user_id,
            owner_id=context.owner_id,
            user_message=context.user_message,
            metadata=metadata,
            tools=context.tools,
        )

    async def _run_agent(
        self,
        agent_name: AgentRole,
        agent_context: AgentContext,
    ) -> AgentRunResult:
        agent = self._agent_pool.get(agent_name)
        if not agent:
            raise ValueError(f'未知 Agent: {agent_name}')
        return await agent.act(agent_context)

    def _dispatch_from_result(self, result: AgentRunResult) -> AgentDispatch:
        return AgentDispatch(
            sender=result.sender,
            agent=result.agent,
            content=result.content,
            message_id=result.message_id,
        )

    # 向调度结果和流式通道发送状态型消息，用于提示前端当前进度
    async def _emit_status(
        self,
        dispatches: list[AgentDispatch],
        session_id: str,
        content: str,
    ) -> None:
        message_id = self._new_message_id()
        dispatches.append(
            AgentDispatch(sender='status', agent='Mike', content=content, message_id=message_id)
        )
        await publish_status(
            content=content,
            agent='Mike',
            message_id=message_id,
        )

    def _extract_agent_hint(self, text: str, candidates: list[AgentRole]) -> Optional[AgentRole]:
        if not candidates:
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

    def _new_message_id(self) -> str:
        return str(uuid4())
