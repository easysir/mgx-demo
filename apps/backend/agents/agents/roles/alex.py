from __future__ import annotations

import re
from typing import Any, Dict, List

from ..base import AgentContext, BaseAgent
from ...llm import get_llm_service
from ...prompts import ALEX_SYSTEM_PROMPT
from ...tools import ToolExecutionError


FILE_BLOCK_PATTERN = re.compile(
    r"```file:(?P<header>[^\n]+)\n(?P<body>.*?)```", re.DOTALL | re.IGNORECASE
)


class AlexAgent(BaseAgent):
    """Engineer responsible for实现与部署，并可写入代码文件。"""

    def __init__(self) -> None:
        super().__init__(name='Alex', description='Engineer')
        self._llm = get_llm_service()

    async def plan(self, context: AgentContext) -> str:
        return 'Alex 正在拆解开发任务与工具调用顺序。'

    async def act(self, context: AgentContext) -> str:
        prompt = ALEX_SYSTEM_PROMPT.format(user_message=context.user_message)
        raw = await self._llm.generate(prompt=prompt, provider='deepseek')
        files = self._extract_file_blocks(raw)
        if not files or not context.tools:
            return raw

        applied = []
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
                    },
                )
                applied.append(result['path'])
            except ToolExecutionError as exc:
                applied.append(f"{spec['path']} (失败: {exc})")

        summary = raw
        if applied:
            summary += '\n\n[文件写入]\n' + '\n'.join(f"- {path}" for path in applied)
        return summary

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
