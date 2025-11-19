"""Base class shared by all agents.

这个模块定义了 Agent 在运行时的标准接口，确保每个角色都能以一致的方式接收上下文、规划任务并输出结果。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from shared.types import AgentRole, SenderRole

from ..llm import LLMProviderError, get_llm_service
from ..tools import ToolExecutor
from ..stream import publish_error, publish_token
from ..context.models import ActionLogEntry, TodoEntry
from ..utils.llm_logger import record_llm_interaction

_CONTEXT_LOG_PATH = Path(__file__).resolve().parents[3] / 'data' / 'agent_context_logs.jsonl'


@dataclass(frozen=True)
class AgentRunResult:
    """标准化的 Agent 执行结果，方便 orchestrator 统一落盘。"""

    agent: AgentRole
    sender: SenderRole
    content: str
    message_id: str


@dataclass
class AgentContext:
    """Runtime context injected into each agent.

    运行时上下文会携带会话、用户和当前输入等信息，方便 Agent 在不共享状态的情况下读取所需数据。
    """

    session_id: str  # 当前对话/沙箱的唯一标识，驱动上下文隔离
    user_id: str  # 发起本轮指令的用户 ID，可用于个性化提示
    owner_id: str  # 会话实际归属者（方便共享/代办场景）
    user_message: str  # 用户本轮输入，用于生成回复或指令
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外上下文（历史摘要、配置等）
    tools: Optional[ToolExecutor] = None  # 可选工具执行器，支持文件写入等动作
    history: str = ''
    artifacts: str = ''
    files_overview: str = ''
    action_log: List[ActionLogEntry] = field(default_factory=list)
    pending_todos: List[TodoEntry] = field(default_factory=list)
    system_prompt: Optional[str] = None
    agent_data: Dict[str, Any] = field(default_factory=dict)
    agent_specific: Dict[AgentRole, Dict[str, Any]] = field(default_factory=dict)

    def for_agent(
        self,
        agent: AgentRole,
        *,
        system_prompt: Optional[str] = None,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> 'AgentContext':
        agent_payload = dict(self.agent_specific.get(agent, {}))
        if overrides:
            agent_payload.update(overrides)
        return AgentContext(
            session_id=self.session_id,
            user_id=self.user_id,
            owner_id=self.owner_id,
            user_message=self.user_message,
            metadata=self.metadata,
            tools=self.tools,
            history=self.history,
            artifacts=self.artifacts,
            files_overview=self.files_overview,
            action_log=self.action_log,
            pending_todos=self.pending_todos,
            system_prompt=system_prompt or self.system_prompt,
            agent_data=agent_payload,
            agent_specific=self.agent_specific,
        )


class BaseAgent:
    """Base behaviour that concrete agents can extend.

    基类约定了 plan/act/report 生命周期，具体角色可按需覆写，从而保持协作流程统一。
    """

    name: AgentRole

    def __init__(self, *, name: AgentRole, description: str) -> None:
        self.name = name
        self.description = description
        self._llm = get_llm_service()

    async def plan(self, context: AgentContext) -> str:
        """Optional planning step before执行工具。"""
        raise NotImplementedError

    async def act(self, context: AgentContext) -> AgentRunResult:
        """Execute核心逻辑，例如调用LLM或工具。"""
        raise NotImplementedError

    async def report(self, context: AgentContext, result: str) -> str:
        """整理输出给 Mike/用户。"""
        return result

    async def _stream_llm_response(
        self,
        *,
        context: AgentContext,
        prompt: str,
        provider: str,
        sender: SenderRole,
        final_transform: Optional[Callable[[str], str]] = None,
        interaction: str = 'act',
    ) -> AgentRunResult:
        """统一的 LLM 流式封装，方便各角色直接调用。"""

        message_id = self._new_message_id()
        chunks: list[str] = []
        try:
            async for chunk in self._llm.stream_generate(prompt=prompt, provider=provider):
                chunks.append(chunk)
                await publish_token(
                    sender=sender,
                    agent=self.name,
                    content=chunk,
                    message_id=message_id,
                    final=False,
                )
            full_text = ''.join(chunks)
            final_text = final_transform(full_text) if final_transform else full_text
            await record_llm_interaction(
                session_id=context.session_id,
                agent=str(self.name),
                prompt=prompt,
                provider=provider,
                raw_response=full_text,
                final_response=final_text,
                interaction=interaction,
            )
            final_timestamp = datetime.now(timezone.utc).isoformat()
            await publish_token(
                sender=sender,
                agent=self.name,
                content=final_text,
                message_id=message_id,
                final=True,
                persist_final=True,
                timestamp=final_timestamp,
            )
            return AgentRunResult(agent=self.name, sender=sender, content=final_text, message_id=message_id)
        except LLMProviderError as exc:
            await publish_error(
                content=str(exc),
                agent=self.name,
                message_id=message_id,
            )
            raise

    async def _emit_final_message(
        self,
        *,
        content: str,
        sender: SenderRole,
    ) -> AgentRunResult:
        message_id = self._new_message_id()
        await publish_token(
            sender=sender,
            agent=self.name,
            content=content,
            message_id=message_id,
            final=True,
            persist_final=True,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return AgentRunResult(agent=self.name, sender=sender, content=content, message_id=message_id)

    def _new_message_id(self) -> str:
        return str(uuid4())

    def _compose_user_message(self, context: AgentContext) -> str:
        metadata = context.metadata or {}
        sections: list[str] = []
        history = context.history or metadata.get('history')
        if history:
            sections.append(f"最近对话（供参考）:\n{history}")
        artifacts = context.artifacts or metadata.get('artifacts')
        artifacts_summary = self._summarize_recent_writes(artifacts)
        if artifacts_summary:
            sections.append(f"近期文件写入（供参考）:\n{artifacts_summary}")
        files_overview = context.files_overview or metadata.get('files_overview') or metadata.get('files')
        if files_overview:
            sections.append(f"沙箱文件概览:\n{files_overview}")
        if context.action_log:
            log_lines = '\n'.join(
                f"- [{entry.status}] {entry.agent} {entry.action}: {entry.result}"
                for entry in context.action_log
            )
            sections.append(f"关键动作回顾:\n{log_lines}")
        if context.pending_todos:
            todo_lines = '\n'.join(
                f"- ({todo.priority}) {todo.description} [{todo.status}]"
                for todo in context.pending_todos
            )
            sections.append(f"重要遗留事项:\n{todo_lines}")
        if context.agent_data:
            agent_lines = '\n'.join(f"- {key}: {value}" for key, value in context.agent_data.items())
            sections.append(f"{self.name} 专属提示:\n{agent_lines}")
        sections.append(f"当前用户输入:\n{context.user_message}")
        return '\n\n'.join(sections)

    def _format_context_for_log(self, context: AgentContext, *, stage: str, preview: int = 200) -> str:
        # 生成结构化上下文快照，后续用于 JSONL 持久化与 debug
        payload = {
            'agent': str(self.name),
            'stage': stage,
            'session_id': context.session_id,
            'owner_id': context.owner_id,
            'user_id': context.user_id,
            'user_message': context.user_message,
            'history_preview': (context.history or '')[:preview],
            'artifacts': context.artifacts,
            'files_overview': context.files_overview,
            'action_log_entries': len(context.action_log),
            'pending_todos': self._summarize_todos_for_log(context.pending_todos),
        }
        self._persist_context_log(payload)
        return json.dumps(payload, ensure_ascii=False)

    def _persist_context_log(self, payload: Dict[str, Any]) -> None:
        # 将上下文快照写入 data/agent_context_logs.jsonl（失败时忽略）
        try:
            _CONTEXT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with _CONTEXT_LOG_PATH.open('a', encoding='utf-8') as handle:
                handle.write(json.dumps(payload, ensure_ascii=False) + '\n')
        except Exception:
            # Logging/persistence failure shouldn't break agent flow
            pass

    def _summarize_todos_for_log(self, todos: List[TodoEntry], *, limit: int = 5) -> Dict[str, Any]:
        # 精简 TODO 列表：返回总数 + 去重后的少量高优条目
        total = len(todos)
        unique: list[str] = []
        highlights: list[Dict[str, Any]] = []
        for todo in todos:
            desc = (todo.description or '').strip()
            if not desc or desc in unique:
                continue
            unique.append(desc)
            highlights.append(
                {
                    'description': desc,
                    'priority': todo.priority,
                    'status': todo.status,
                }
            )
            if len(highlights) >= limit:
                break
        return {
            'total': total,
            'highlights': highlights,
            'truncated': total > len(highlights),
        }

    def _summarize_recent_writes(self, artifacts_text: Optional[str], limit: int = 5) -> str:
        if not artifacts_text:
            return ''
        summaries: list[str] = []
        for line in artifacts_text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            stripped = stripped.lstrip('-').strip()
            if not stripped:
                continue
            label = ''
            path = stripped
            if ': ' in stripped:
                label, path = stripped.split(': ', 1)
            label = label.strip()
            path = path.strip()
            if not path:
                continue
            filename = path.split('/')[-1] or path
            summary = f"{filename}: {path}"
            if label:
                summary += f"（{label}）"
            summaries.append(summary)
            if len(summaries) >= limit:
                break
        if not summaries:
            return ''
        return '\n'.join(f"- {item}" for item in summaries)
