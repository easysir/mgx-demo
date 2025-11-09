"""Default sequential workflow: Mike → team status → Alex, etc."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from shared.types import AgentRole, SenderRole

from ..config import AgentRegistry
from ..llm import LLMService
from ..runtime.orchestrator import AgentDispatch, AgentWorkflow, WorkflowContext


@dataclass(frozen=True)
class WorkflowStage:
    sender: SenderRole
    agent: Optional[AgentRole]
    template: Optional[str] = None
    prompt: Optional[str] = None
    provider: Optional[str] = None

    async def render(self, context: WorkflowContext, llm_service: LLMService) -> AgentDispatch:
        if self.prompt:
            prompt = self.prompt.format(user_message=context.user_message)
            content = await llm_service.generate(prompt=prompt, provider=self.provider)
        elif self.template:
            content = self.template.format(user_message=context.user_message)
        else:
            content = ''
        return AgentDispatch(sender=self.sender, agent=self.agent, content=content)


class DefaultWorkflow(AgentWorkflow):
    """MVP workflow that mimics Mike coordinating Alex."""

    def __init__(self, llm_service: LLMService) -> None:
        self._llm_service = llm_service
        self._stages = [
            WorkflowStage(
                sender='status',
                agent='Mike',
                template='Mike 正在评估任务，准备调度团队。',
            ),
            WorkflowStage(
                sender='mike',
                agent='Mike',
                prompt='You are Mike, a team lead. Briefly向用户说明你如何处理中 "{user_message}".',
                provider='openai',
            ),
            WorkflowStage(
                sender='status',
                agent='Alex',
                template='Alex 已接手任务，开始在沙箱内修改代码。',
            ),
            WorkflowStage(
                sender='agent',
                agent='Alex',
                prompt='You are Alex, an engineer. 用中文总结你刚完成的实现，基于 "{user_message}"。',
                provider='gemini',
            ),
        ]

    async def generate(self, context: WorkflowContext, registry: AgentRegistry) -> list[AgentDispatch]:
        dispatches: list[AgentDispatch] = []
        for stage in self._stages:
            if stage.agent and not registry.is_enabled(stage.agent):
                continue
            dispatches.append(await stage.render(context, self._llm_service))
        return dispatches
