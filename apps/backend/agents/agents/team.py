"""Placeholder agent implementations for Phase 1."""

from __future__ import annotations

from typing import Dict, Type

from .base import AgentContext, BaseAgent
from shared.types import AgentRole


class StaticAgent(BaseAgent):
    """Lightweight agent that returns scripted content until LLM接入."""

    scripted_response: str = ''

    async def plan(self, context: AgentContext) -> str:
        return f"{self.name} 已收到需求：{context.user_message}"

    async def act(self, context: AgentContext) -> str:
        return self.scripted_response or f"{self.name} 正在处理：{context.user_message}"


class MikeAgent(StaticAgent):
    scripted_response = 'Mike：需求已记录，会协调团队执行。'


class EmmaAgent(StaticAgent):
    scripted_response = 'Emma：已整理需求列表，准备交给 Bob。'


class BobAgent(StaticAgent):
    scripted_response = 'Bob：架构草案完成，Alex 可以继续开发。'


class AlexAgent(StaticAgent):
    scripted_response = 'Alex：代码修改完成，如需进一步优化请告知。'


class DavidAgent(StaticAgent):
    scripted_response = 'David：数据分析结果就绪，可用于可视化。'


class IrisAgent(StaticAgent):
    scripted_response = 'Iris：已收集最新资料，供团队参考。'


AGENT_CLASS_MAP: Dict[AgentRole, Type[BaseAgent]] = {
    'Mike': MikeAgent,
    'Emma': EmmaAgent,
    'Bob': BobAgent,
    'Alex': AlexAgent,
    'David': DavidAgent,
    'Iris': IrisAgent,
}
