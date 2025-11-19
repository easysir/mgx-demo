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
from ..context import build_session_context, build_agent_context_view
from ..agents.base import AgentContext, AgentRunResult
from ..agents.roles.alex import AlexAgent
from ..agents.roles.bob import BobAgent
from ..agents.roles.david import DavidAgent
from ..agents.roles.emma import EmmaAgent
from ..agents.roles.iris import IrisAgent
from ..agents.roles.mike import MikeAgent
from ..stream import publish_status
from ..context.models import ActionLogEntry, TodoEntry
from ..context.state import (
    add_todo,
)

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
        # 获取 SessionContext 快照，供各 Agent 构建视图
        current_session_context = context.session_context
        # 构建初始 AgentContext 视图
        agent_context = build_agent_context_view(
            session_id=context.session_id,
            owner_id=context.owner_id,
            user_id=context.user_id,
            user_message=context.user_message,
            tools=context.tools,
            session_context=current_session_context,
        )
        task_focus = self._resolve_task_focus(context)
        # Mike 专用 AgentContext 视图
        mike_context = agent_context.for_agent('Mike')
        # 收集每个 Agent 的输出，供 Mike 最终汇总向用户汇报
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

            # 构建当前 Agent 的 AgentContext 视图
            agent_view = agent_context.for_agent(next_agent)

            agent_result = await self._run_agent(next_agent, agent_view)
            agent_contributions.append((next_agent, agent_result.content))
            step_index = len(agent_context.action_log) + 1
            # detail_path = persist_action_detail(
            #     context.session_id,
            #     step_index,
            #     {
            #         'agent': next_agent,
            #         'action': 'agent_execution',
            #         'content': agent_result.content,
            #         'timestamp': datetime.now(timezone.utc).isoformat(),
            #     },
            # )
            todos = self._extract_todos(agent_result.content)
            summary_line = self._summarize_agent_result(
                agent=next_agent,
                text=agent_result.content,
                task_focus=task_focus,
                todos=todos,
            )

            log_entry = ActionLogEntry(
                agent=next_agent,
                action='agent_execution',
                result=agent_result.content[:400],
                status='success',
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata={
                    'summary_line': summary_line,
                    'detail_path': '',
                    'step_id': step_index,
                },
            )
            agent_context.action_log.append(log_entry)

            # record_action(context.session_id, log_entry)

            # todo 后续整体收敛到 context 中，作为上下文管理的一部分
            for description in todos:
                todo_entry = TodoEntry(
                    description=description,
                    owner=next_agent,
                    priority='high',
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
                agent_context.pending_todos.append(todo_entry)
                add_todo(context.session_id, todo_entry)

            # 重新构建 SessionContext 快照 后续轮次使用
            current_session_context = build_session_context(
                session_id=context.session_id,
                owner_id=context.owner_id,
                user_id=context.user_id,
                user_message=context.user_message,
            )

            # todo 下面3条后续删掉； 用户历史消息 和 上下文 以及 上下文持久化（恢复） 统一收敛到 Context 模块？
            # snapshot_path = persist_session_context_snapshot(context.session_id, current_session_context, step_index)
            # log_entry.metadata['context_snapshot'] = snapshot_path
            # attach_snapshot_to_last_action(context.session_id, snapshot_path)
            
            agent_context = build_agent_context_view(
                session_id=context.session_id,
                owner_id=context.owner_id,
                user_id=context.user_id,
                user_message=context.user_message,
                tools=context.tools,
                session_context=current_session_context,
            )
            mike_context = agent_context.for_agent('Mike')

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

    def _resolve_task_focus(self, context: WorkflowContext) -> str:
        session_ctx = context.session_context
        if session_ctx and session_ctx.most_recent_user_message:
            return session_ctx.most_recent_user_message.strip()
        return (context.user_message or '').strip()

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
    
    # todo 后续整体收敛到 context 模块中
    def _summarize_agent_result(
        self,
        *,
        agent: AgentRole,
        text: str,
        task_focus: str = '',
        todos: Optional[list[str]] = None,
        limit: int = 200,
    ) -> str:
        core_statement = self._extract_primary_statement(text)
        file_summary = self._extract_file_summary(text)
        command_summary = self._extract_command_summary(text)
        todo_line = ''
        if todos:
            preview = '; '.join(todos[:2])
            if len(todos) > 2:
                preview += f' 等{len(todos)}项'
            todo_line = f"TODO {preview}"
        parts = []
        task_focus = (task_focus or '').strip()
        if task_focus:
            parts.append(f"围绕“{task_focus}”")
        if core_statement:
            parts.append(core_statement)
        if file_summary:
            parts.append(file_summary)
        if command_summary:
            parts.append(command_summary)
        if todo_line:
            parts.append(todo_line)
        sentence = f"{agent}: " + '；'.join(parts) if parts else f"{agent}: 无有效输出"
        return sentence[: limit - 3] + '...' if len(sentence) > limit else sentence

    def _extract_primary_statement(self, text: str) -> str:
        # 扫描 agent 输出的每一行，跳过提示性/列表/工具标签，取第一句可读文本
        for raw in text.splitlines():
            stripped = raw.strip()
            if not stripped:
                continue
            if stripped.startswith('['):
                continue
            if stripped.startswith('- '):
                continue
            if stripped.startswith('##'):
                stripped = stripped.lstrip('# ').strip()
            return stripped
        return ''

    def _extract_file_summary(self, text: str, limit: int = 2) -> str:
        markers = ('[文件写入', '[PRD 写入', '[架构文档写入')
        collecting = False
        files: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                collecting = False
                continue
            if stripped.startswith('['):
                collecting = any(stripped.startswith(marker) for marker in markers)
                continue
            if collecting and stripped.startswith('- '):
                path = stripped.lstrip('- ').split(' (')[0].strip()
                if path:
                    files.append(path)
            elif collecting and not stripped.startswith('- '):
                collecting = False
        if not files:
            return ''
        display = ', '.join(files[:limit])
        if len(files) > limit:
            display += f" 等{len(files)}个文件"
        return f"产出 {display}"

    def _extract_command_summary(self, text: str, limit: int = 1) -> str:
        marker = '[Sandbox Shell 执行'
        collecting = False
        commands: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                collecting = False
                continue
            if stripped.startswith(marker):
                collecting = True
                continue
            if stripped.startswith('[') and stripped != marker:
                collecting = False
                continue
            if collecting:
                if stripped.startswith('- '):
                    commands.append(stripped[2:].strip())
                continue
        if not commands:
            return ''
        preview = '; '.join(commands[:limit])
        if len(commands) > limit:
            preview += f" 等{len(commands)}次命令"
        return f"执行 {preview}"
