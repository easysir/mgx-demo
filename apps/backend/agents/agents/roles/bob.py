from __future__ import annotations

import re
from typing import Any, Dict, List

from ..base import AgentContext, AgentRunResult, BaseAgent, StreamPublisher
from ...prompts import BOB_SYSTEM_PROMPT
from ...tools import ToolExecutionError
from ...llm import LLMProviderError
from ...utils import extract_file_blocks


class BobAgent(BaseAgent):
    """Architect in charge of技术方案。"""

    def __init__(self) -> None:
        super().__init__(name='Bob', description='Architect')

    async def plan(self, context: AgentContext) -> str:
        return 'Bob 正在评估架构与技术栈。'

    async def act(
        self, context: AgentContext, stream_publisher: StreamPublisher | None = None
    ) -> AgentRunResult:
        prompt = BOB_SYSTEM_PROMPT.format(user_message=self._compose_user_message(context))
        message_id = self._new_message_id()
        chunks: list[str] = []
        try:
            async for chunk in self._llm.stream_generate(prompt=prompt, provider='deepseek'):
                chunks.append(chunk)
                if stream_publisher:
                    await stream_publisher(
                        {
                            'type': 'token',
                            'sender': 'agent',
                            'agent': self.name,
                            'content': chunk,
                            'message_id': message_id,
                            'final': False,
                        }
                    )
            raw = ''.join(chunks)
            reference_blocks = self._extract_read_blocks(raw)
            history_paths = self._discover_shared_paths(context)
            combined_refs = list(dict.fromkeys(reference_blocks + history_paths))
            references = ''
            if combined_refs and context.tools:
                references = await self._inject_references(combined_refs, context=context)
            summary = f"{references}\n\n{raw}".strip() if references else raw
            files = extract_file_blocks(raw)
            applied: list[str] = []
            if files and context.tools:
                for spec in files:
                    try:
                        result = await context.tools.run(
                            'file_write',
                            params={
                                'session_id': context.session_id,
                                'owner_id': context.owner_id,
                                'path': spec['path'],
                                'content': spec['content'],
                                'append': spec['mode'] == 'append',
                                'overwrite': spec['mode'] == 'overwrite',
                                'agent': self.name,
                            },
                        )
                        applied.append(result['path'])
                    except ToolExecutionError as exc:
                        applied.append(f"{spec['path']} (失败: {exc})")
            if applied:
                summary += '\n\n[架构文档写入]\n' + '\n'.join(f"- {path}" for path in applied)
            if stream_publisher:
                await stream_publisher(
                    {
                        'type': 'token',
                        'sender': 'agent',
                        'agent': self.name,
                        'content': summary,
                        'message_id': message_id,
                        'final': True,
                    }
                )
            return AgentRunResult(agent=self.name, sender='agent', content=summary, message_id=message_id)
        except LLMProviderError as exc:
            if stream_publisher:
                await stream_publisher(
                    {
                        'type': 'error',
                        'sender': 'status',
                        'agent': self.name,
                        'content': str(exc),
                        'message_id': message_id,
                        'final': True,
                    }
                )
            raise

    def _extract_read_blocks(self, text: str) -> List[str]:
        return [match.group('path').strip() for match in re.finditer(r"\{\{read_file:(?P<path>[^\}]+)\}\}", text) if match.group('path').strip()]

    def _discover_shared_paths(self, context: AgentContext) -> List[str]:
        metadata = context.metadata or {}
        artifacts = metadata.get('artifacts', '')
        history = metadata.get('history', '')
        corpus = '\n'.join(filter(None, [artifacts, history]))
        if not corpus:
            return []
        paths: List[str] = []
        for line in corpus.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            candidate = stripped.lstrip('-').split(':')[-1].strip()
            if not candidate:
                continue
            candidate = candidate.split(' (')[0].strip()
            if '/' in candidate or candidate.endswith('.md') or candidate.endswith('.txt'):
                paths.append(candidate)
        return paths

    async def _inject_references(self, paths: List[str], *, context: AgentContext) -> str:
        snippets: List[str] = []
        for path in paths:
            try:
                payload = await context.tools.run(
                    'file_read',
                    params={
                        'session_id': context.session_id,
                        'owner_id': context.owner_id,
                        'path': path,
                        'agent': self.name,
                    },
                )
                content = payload.get('content')
                if content:
                    snippets.append(f"### 引用自 {path}\n{content.strip()}")
            except ToolExecutionError as exc:
                snippets.append(f"### 引用自 {path} 失败\n原因: {exc}")
        return '\n\n'.join(snippets)
