from __future__ import annotations

from ..base import AgentContext, AgentRunResult, BaseAgent, StreamPublisher
from ...prompts import IRIS_SYSTEM_PROMPT
from ...tools import ToolExecutionError


class IrisAgent(BaseAgent):
    """Researcher responsible for external intelligence gathering."""

    def __init__(self) -> None:
        super().__init__(name='Iris', description='Researcher')

    async def plan(self, context: AgentContext) -> str:
        return 'Iris 正在搜索资料与外部参考。'

    async def act(
        self, context: AgentContext, stream_publisher: StreamPublisher | None = None
    ) -> AgentRunResult:
        research_snippets = await self._collect_external_insights(context)
        prompt = IRIS_SYSTEM_PROMPT.format(
            user_message=self._compose_user_message(context),
            research_snippets=research_snippets,
        )
        return await self._stream_llm_response(
            context=context,
            prompt=prompt,
            provider='deepseek',
            sender='agent',
            stream_publisher=stream_publisher,
        )

    async def _collect_external_insights(self, context: AgentContext) -> str:
        if not context.tools:
            return '（工具不可用，使用已有知识给出参考）'
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
            return '（web_search 未返回可引用的结果）'

        lines = []
        for item in entries[:3]:
            title = item.get('title') or 'Untitled'
            snippet = item.get('snippet') or ''
            url = item.get('url') or ''
            lines.append(f"- {title}: {snippet} (Source: {url})".strip())
        return '\n'.join(lines) if lines else '（web_search 未找到可引用的结果）'
