from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from ..base import AgentContext, AgentRunResult, BaseAgent
from ..prompts import ALEX_SYSTEM_PROMPT
from ...tools import ToolExecutionError
from ...llm import LLMProviderError
from ...utils import extract_file_blocks, extract_shell_blocks
from ...utils.llm_logger import record_llm_interaction
from ...stream import publish_error, publish_status, publish_token


class AlexAgent(BaseAgent):
    """Engineer responsible for实现与部署，并可写入代码文件。"""

    def __init__(self) -> None:
        super().__init__(name='Alex', description='Engineer')

    async def plan(self, context: AgentContext) -> str:
        return 'Alex 正在拆解开发任务与工具调用顺序。'

    async def act(self, context: AgentContext) -> AgentRunResult:
        # TODO: remove context logging once pipeline verified
        self._format_context_for_log(context, stage='act')
        prompt = ALEX_SYSTEM_PROMPT.format(user_message=self._compose_user_message(context))
        message_id = self._new_message_id()
        chunks: list[str] = []
        try:
            async for chunk in self._llm.stream_generate(prompt=prompt, provider='deepseek'):
                chunks.append(chunk)
                await publish_token(
                    sender='agent',
                    agent=self.name,
                    content=chunk,
                    message_id=message_id,
                    final=False,
                )
            raw = ''.join(chunks)
            files = extract_file_blocks(raw)
            commands = extract_shell_blocks(raw)
            summary = raw
            applied: list[str] = []
            executed: list[str] = []
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
            if commands and context.tools:
                for spec in commands:
                    try:
                        params = {
                            'session_id': context.session_id,
                            'owner_id': context.owner_id,
                            'command': spec['command'],
                            'agent': self.name,
                        }
                        if spec.get('cwd'):
                            params['cwd'] = str(spec['cwd'])
                        if spec.get('timeout'):
                            params['timeout'] = int(spec['timeout'])
                        env = spec.get('env') or {}
                        if env:
                            params['env'] = {str(key): str(value) for key, value in env.items()}
                        result = await context.tools.run('sandbox_shell', params=params)
                        stdout = (result.get('stdout') or '').strip()
                        stderr = (result.get('stderr') or '').strip()
                        log_line = f"$ {result['command']} (exit {result['exit_code']})"
                        preview = log_line
                        if stdout:
                            preview += f"\nstdout:\n{stdout[:400]}"
                        if stderr:
                            preview += f"\nstderr:\n{stderr[:400]}"
                        executed.append(preview.strip())
                        status_id = self._new_message_id()
                        await publish_status(
                            content=preview,
                            agent=self.name,
                            message_id=status_id,
                            timestamp=datetime.now(timezone.utc).isoformat(),
                        )
                    except ToolExecutionError as exc:
                        error_line = f"{spec['command']} (失败: {exc})"
                        executed.append(error_line)
                        status_id = self._new_message_id()
                        await publish_status(
                            content=error_line,
                            agent=self.name,
                            message_id=status_id,
                            timestamp=datetime.now(timezone.utc).isoformat(),
                        )
            if applied:
                summary += '\n\n[文件写入]\n' + '\n'.join(f"- {path}" for path in applied)
            if executed:
                summary += '\n\n[Sandbox Shell 执行]\n' + '\n'.join(f"- {entry}" for entry in executed)
            await record_llm_interaction(
                session_id=context.session_id,
                agent=str(self.name),
                prompt=prompt,
                provider='deepseek',
                raw_response=raw,
                final_response=summary,
                interaction='act',
            )
            await publish_token(
                sender='agent',
                agent=self.name,
                content=summary,
                message_id=message_id,
                final=True,
                persist_final=True,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            return AgentRunResult(agent=self.name, sender='agent', content=summary, message_id=message_id)
        except LLMProviderError as exc:
            await publish_error(
                content=str(exc),
                agent=self.name,
                message_id=message_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            raise
