from __future__ import annotations

from typing import Any, Dict, List

from ..base import AgentContext, AgentRunResult, BaseAgent, StreamPublisher
from ...prompts import ALEX_SYSTEM_PROMPT
from ...tools import ToolExecutionError
from ...llm import LLMProviderError
from ...utils import extract_file_blocks


class AlexAgent(BaseAgent):
    """Engineer responsible for实现与部署，并可写入代码文件。"""

    def __init__(self) -> None:
        super().__init__(name='Alex', description='Engineer')

    async def plan(self, context: AgentContext) -> str:
        return 'Alex 正在拆解开发任务与工具调用顺序。'

    async def act(
        self, context: AgentContext, stream_publisher: StreamPublisher | None = None
    ) -> AgentRunResult:
        prompt = ALEX_SYSTEM_PROMPT.format(user_message=self._compose_user_message(context))
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
            files = extract_file_blocks(raw)
            summary = raw
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
                            },
                        )
                        applied.append(result['path'])
                    except ToolExecutionError as exc:
                        applied.append(f"{spec['path']} (失败: {exc})")
            if applied:
                summary += '\n\n[文件写入]\n' + '\n'.join(f"- {path}" for path in applied)
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
