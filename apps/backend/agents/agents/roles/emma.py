from __future__ import annotations

import re
from typing import Any, Dict, List

from ..base import AgentContext, AgentRunResult, BaseAgent, StreamPublisher
from ...prompts import EMMA_SYSTEM_PROMPT
from ...tools import ToolExecutionError
from ...llm import LLMProviderError

FILE_BLOCK_PATTERN = re.compile(
    r"```file:(?P<header>[^\n]+)\n(?P<body>.*?)```", re.DOTALL | re.IGNORECASE
)


class EmmaAgent(BaseAgent):
    """Product manager focusing on需求分析。"""

    def __init__(self) -> None:
        super().__init__(name='Emma', description='Product Manager')

    async def plan(self, context: AgentContext) -> str:
        return 'Emma 正在整理功能列表与验收标准。'

    async def act(
        self, context: AgentContext, stream_publisher: StreamPublisher | None = None
    ) -> AgentRunResult:
        research_snippets = await self._collect_research(context)
        prompt = EMMA_SYSTEM_PROMPT.format(
            user_message=context.user_message,
            research_snippets=research_snippets,
        )
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
            references = ''
            if reference_blocks and context.tools:
                references = await self._inject_references(reference_blocks, context=context)
            summary = f"{references}\n\n{raw}".strip() if references else raw
            files = self._extract_file_blocks(raw)
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
                summary += '\n\n[PRD 写入]\n' + '\n'.join(f"- {path}" for path in applied)
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

    async def _collect_research(self, context: AgentContext) -> str:
        if not context.tools:
            return '（工具暂不可用）'
        try:
            result = await context.tools.run(
                'web_search',
                params={
                    'session_id': context.session_id,
                    'owner_id': context.owner_id,
                    'agent': self.name,
                    'query': context.user_message,
                    'max_results': 3,
                },
            )
        except ToolExecutionError as exc:
            return f'（web_search 失败: {exc}）'
        entries = result.get('results') if isinstance(result, dict) else None
        if not entries:
            return '（未检索到可引用的外部资料）'
        lines = []
        for item in entries[:3]:
            title = item.get('title') or 'Untitled'
            snippet = item.get('snippet') or ''
            url = item.get('url') or ''
            lines.append(f"- {title}: {snippet} (Source: {url})".strip())
        return '\n'.join(lines) if lines else '（未检索到可引用的外部资料）'

    def _extract_file_blocks(self, text: str) -> List[Dict[str, Any]]:
        specs: List[Dict[str, Any]] = []
        for match in FILE_BLOCK_PATTERN.finditer(text):
            header = match.group('header').strip()
            body = match.group('body')
            if not body:
                continue
            segments = header.split()
            path = segments[0]
            mode = 'overwrite'
            for token in segments[1:]:
                lowered = token.lower()
                if lowered in {'append', 'overwrite'}:
                    mode = lowered
            specs.append(
                {
                    'path': path,
                    'mode': mode,
                    'content': body.strip(),
                }
            )
        return specs

    def _extract_read_blocks(self, text: str) -> List[str]:
        return [
            match.group('path').strip()
            for match in re.finditer(r"\{\{read_file:(?P<path>[^\}]+)\}\}", text)
            if match.group('path').strip()
        ]

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
                snippets.append(f"### 引用 {path} 失败\n原因: {exc}")
        return '\n\n'.join(snippets)
