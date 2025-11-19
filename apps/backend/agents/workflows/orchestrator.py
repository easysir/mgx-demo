"""State-machine orchestrator describing Mike-led dynamic task routing with streaming."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from shared.types import AgentRole

from ..config import AgentRegistry
from ..runtime.executor import AgentWorkflow, WorkflowContext
from ..agents.base import AgentContext, AgentRunResult
from ..agents.roles.alex import AlexAgent
from ..agents.roles.bob import BobAgent
from ..agents.roles.david import DavidAgent
from ..agents.roles.emma import EmmaAgent
from ..agents.roles.iris import IrisAgent
from ..agents.roles.mike import MikeAgent
from ..stream import publish_status
from ..context.models import ActionLogEntry, TodoEntry
from ..context.state import record_action, add_todo

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
    ) -> None:
        available_agents = [agent for agent in AGENT_EXECUTION_ORDER if registry.is_enabled(agent)]
        available_agents_descriptions = registry.describe_agents(available_agents)
        agent_context = self._build_agent_context(context)
        mike_context = agent_context.for_agent('Mike')
        agent_contributions: list[Tuple[AgentRole, str]] = []

        await self._emit_status(
            context.session_id,
            'Mike 正在评估任务，准备调度团队。',
        )

        plan_result = await self._mike_agent.plan_next_agent(mike_context, available_agents_descriptions)
        next_agent = self._extract_agent_hint(plan_result.content, available_agents)

        iterations = 0
        
        while next_agent and iterations < self.MAX_ITERATIONS:
            iterations += 1
            await self._emit_status(
                context.session_id,
                f'Mike 将任务交给 {next_agent}。',
            )

            agent_result = await self._run_agent(next_agent, agent_context.for_agent(next_agent))
            agent_contributions.append((next_agent, agent_result.content))
            log_entry = ActionLogEntry(
                agent=next_agent,
                action='agent_execution',
                result=agent_result.content[:400],
                status='success',
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            agent_context.action_log.append(log_entry)
            record_action(context.session_id, log_entry)
            for description in self._extract_todos(agent_result.content):
                todo_entry = TodoEntry(
                    description=description,
                    owner=next_agent,
                    priority='high',
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
                agent_context.pending_todos.append(todo_entry)
                add_todo(context.session_id, todo_entry)

            available_agents = [agent for agent in available_agents if agent != next_agent]
            review_result = await self._mike_agent.review_agent_output(
                mike_context,
                next_agent,
                agent_result.content,
                available_agents,
            )

            next_agent = self._extract_agent_hint(review_result.content, available_agents)

        await self._emit_status(
            context.session_id,
            'Mike 收齐团队结果，准备向用户汇报结论与下一步。',
        )
        await self._mike_agent.summarize_team(mike_context, agent_contributions)
        return None

    def _build_agent_context(self, context: WorkflowContext) -> AgentContext:
        session_context = context.session_context
        metadata: Dict[str, Any] = {}
        history = ''
        artifacts = ''
        files_overview = ''
        action_log = []
        pending = []
        agent_data: Dict[str, Any] = {}
        agent_specific: Dict[AgentRole, Dict[str, Any]] = {}
        if session_context:
            metadata.update(session_context.to_metadata_payload())
            history = session_context.conversation_history
            artifacts = session_context.artifacts
            files_overview = session_context.files_overview
            action_log = session_context.action_log
            pending = session_context.pending_todos
            agent_specific = session_context.agent_specific
        return AgentContext(
            session_id=context.session_id,
            user_id=context.user_id,
            owner_id=context.owner_id,
            user_message=context.user_message,
            metadata=metadata,
            tools=context.tools,
            history=history,
            artifacts=artifacts,
            files_overview=files_overview,
            action_log=action_log,
            pending_todos=pending,
            agent_data=agent_data,
            agent_specific=agent_specific,
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

    # 向调度结果和流式通道发送状态型消息，用于提示前端当前进度
    async def _emit_status(
        self,
        session_id: str,
        content: str,
    ) -> None:
        message_id = self._new_message_id()
        await publish_status(
            content=content,
            agent='Mike',
            message_id=message_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
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

    def _extract_todos(self, text: str) -> list[str]:
        todos: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            lowered = stripped.lower()
            if lowered.startswith('todo:'):
                todos.append(stripped[5:].strip())
                continue
            if stripped.startswith('- [ ]'):
                todos.append(stripped.split(']', 1)[-1].strip())
        return todos
