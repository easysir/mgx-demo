"""State-machine orchestrator describing Mike-led dynamic task routing with streaming."""

from __future__ import annotations

import json
import re
from typing import Dict, List, Optional
from uuid import uuid4

from shared.types import AgentRole, SenderRole

from ..config import AgentRegistry
from ..llm import LLMProviderError, LLMService
from ..prompts import SYSTEM_PROMPTS
from ..runtime.executor import AgentDispatch, AgentWorkflow, StreamPublisher, WorkflowContext
from ..agents.base import AgentContext
from ..agents.roles.alex import AlexAgent

AGENT_EXECUTION_ORDER: List[AgentRole] = ['Emma', 'Bob', 'Alex', 'David', 'Iris']
AGENT_PROVIDERS: Dict[AgentRole, str] = {
    'Mike': 'deepseek',
    'Emma': 'deepseek',
    'Bob': 'deepseek',
    'Alex': 'deepseek',
    'David': 'deepseek',
    'Iris': 'deepseek',
}
FINISH_TOKENS = {'finish', '完成', '结束', 'done', 'complete'}

MIKE_PLAN_PROMPT = """\
You are Mike, the MGX team lead. Analyze the user request "{user_message}".
Alex is the only agent that may perform concrete coding or file changes, so route implementation work to Alex whenever code edits are required.
Available agents: {available_agents}. For the next step return JSON:
{{"next_agent": "<Emma|Bob|Alex|David|Iris|finish>", "reason": "<short text>"}}.
Explain decisions clearly in natural language before/after the JSON block."""

MIKE_REVIEW_PROMPT = """\
You are Mike. {agent_name} just reported:
\"\"\"{agent_output}\"\"\"
Based on this result, decide the next agent or finish.
Respond with JSON: {{"next_agent": "<agent|finish>", "decision": "<pass|revise|finish>", "reason": "<text>"}}."""

MIKE_SUMMARY_PROMPT = """\
You are Mike. Summarize the collaboration outcome for "{user_message}".
Include contributions from: {contributors}. Provide next recommended action."""


class SequentialWorkflow(AgentWorkflow):
    """MVP orchestrator that lets Mike 动态指派或结束任务，并支持流式输出."""

    MAX_ITERATIONS = 6

    def __init__(self, llm_service: LLMService) -> None:
        self._llm_service = llm_service
        self._alex_agent = AlexAgent()

    async def generate(
        self,
        context: WorkflowContext,
        registry: AgentRegistry,
        stream_publisher: Optional[StreamPublisher] = None,
    ) -> list[AgentDispatch]:
        dispatches: list[AgentDispatch] = []
        available_agents = [agent for agent in AGENT_EXECUTION_ORDER if registry.is_enabled(agent)]
        # 追踪出现过的 Agent，方便最终 summary
        visited_agents: list[AgentRole] = []
        last_agent_output: Optional[str] = None

        # step1：Mike 先给前端发一个状态提示
        await self._emit_status(
            dispatches,
            context.session_id,
            'Mike 正在评估任务，准备调度团队。',
            stream_publisher,
        )

        # step2：Mike 输出整体 plan，并解析下一位要执行的 Agent
        plan_text, plan_message_id = await self._stream_mike_plan(
            context, available_agents, stream_publisher
        )
        dispatches.append(
            AgentDispatch(sender='mike', agent='Mike', content=plan_text, message_id=plan_message_id)
        )
        next_agent = self._extract_agent_hint(plan_text, available_agents)

        iterations = 0
        # 核心循环：Mike 每次根据上一步点评选择下一位 Agent，直到指令为 finish 或达到迭代上限
        while next_agent and iterations < self.MAX_ITERATIONS:
            iterations += 1  # 控制最大轮数，防止 LLM 冻结或无限调度
            # 进入单个 Agent 的执行周期：先广播状态，再真正运行 Agent
            await self._emit_status(
                dispatches,
                context.session_id,
                f'Mike 将任务交给 {next_agent}。',
                stream_publisher,
            )

            # 执行目标 Agent，收集输出文本以及 message_id（用于前端聚合 token）
            agent_output, agent_message_id = await self._stream_agent_execution(
                next_agent, context, stream_publisher
            )
            dispatches.append(
                AgentDispatch(
                    sender='agent',
                    agent=next_agent,
                    content=agent_output,
                    message_id=agent_message_id,
                )
            )
            visited_agents.append(next_agent)  # 记录贡献者，方便 summary 致谢
            last_agent_output = agent_output  # 备份最近结果，必要时在 summary 中引用

            # 当前 Agent 完成后，从可选列表里移除，避免重复调用
            available_agents = [agent for agent in available_agents if agent != next_agent]
            # Mike 审阅该 Agent 结果，并决定下一步走向（继续/换人/结束）
            review_text, review_message_id = await self._stream_mike_review(
                context, next_agent, agent_output, available_agents, stream_publisher
            )
            dispatches.append(
                AgentDispatch(
                    sender='mike',
                    agent='Mike',
                    content=review_text,
                    message_id=review_message_id,
                )
            )

            # 解析 Mike 的 JSON/自然语言提示，得出下一位 Agent；若 Mike 决定 finish，会返回 None
            next_agent = self._extract_agent_hint(review_text, available_agents)

        # 跳出循环：要么 Mike 主动 finish，要么达到最大轮数，统一广播“收尾”状态
        await self._emit_status(
            dispatches,
            context.session_id,
            'Mike 收齐团队结果，准备向用户汇报结论与下一步。',
            stream_publisher,
        )
        # Mike 基于 visited_agents + 最后一次输出生成总结，并通过流式接口推送给前端
        summary_text, summary_message_id = await self._stream_mike_summary(
            context, visited_agents, last_agent_output, stream_publisher
        )
        dispatches.append(
            AgentDispatch(
                sender='mike',
                agent='Mike',
                content=summary_text,
                message_id=summary_message_id,
            )
        )
        return dispatches

    async def _stream_mike_plan(
        self,
        context: WorkflowContext,
        available_agents: list[AgentRole],
        stream_publisher: Optional[StreamPublisher],
    ) -> tuple[str, str]:
        prompt = MIKE_PLAN_PROMPT.format(
            user_message=context.user_message,
            available_agents=', '.join(available_agents) if available_agents else '暂无可用 Agent',
        )
        message_id = self._new_message_id()
        # 通过流式 LLM 输出，让前端实时看到 Mike 的规划过程
        result = await self._stream_llm_output(
            session_id=context.session_id,
            sender='mike',
            agent_name='Mike',
            prompt=prompt,
            provider=AGENT_PROVIDERS['Mike'],
            stream_publisher=stream_publisher,
            message_id=message_id,
        )
        return result, message_id

    async def _stream_mike_review(
        self,
        context: WorkflowContext,
        agent_name: AgentRole,
        agent_output: str,
        remaining_agents: list[AgentRole],
        stream_publisher: Optional[StreamPublisher],
    ) -> tuple[str, str]:
        # 根据当前 Agent 的输出让 Mike 决策下一步（继续、换人或结束）
        prompt = MIKE_REVIEW_PROMPT.format(agent_name=agent_name, agent_output=agent_output)
        if not remaining_agents:
            prompt += "\n没有剩余 Agent，可考虑 finish。"
        message_id = self._new_message_id()
        result = await self._stream_llm_output(
            session_id=context.session_id,
            sender='mike',
            agent_name='Mike',
            prompt=prompt,
            provider=AGENT_PROVIDERS['Mike'],
            stream_publisher=stream_publisher,
            message_id=message_id,
        )
        return result, message_id

    async def _stream_mike_summary(
        self,
        context: WorkflowContext,
        contributors: list[AgentRole],
        last_agent_output: Optional[str],
        stream_publisher: Optional[StreamPublisher],
    ) -> tuple[str, str]:
        contributor_text = ', '.join(contributors) if contributors else 'Mike'
        prompt = MIKE_SUMMARY_PROMPT.format(user_message=context.user_message, contributors=contributor_text)
        if last_agent_output:
            prompt += f"\n最近一次交付内容：```{last_agent_output}```"
        message_id = self._new_message_id()
        # workflow 结束时统一由 Mike 给用户总结并推荐下一步
        result = await self._stream_llm_output(
            session_id=context.session_id,
            sender='mike',
            agent_name='Mike',
            prompt=prompt,
            provider=AGENT_PROVIDERS['Mike'],
            stream_publisher=stream_publisher,
            message_id=message_id,
        )
        return result, message_id

    async def _stream_agent_execution(
        self,
        agent_name: AgentRole,
        context: WorkflowContext,
        stream_publisher: Optional[StreamPublisher],
    ) -> tuple[str, str]:
        # 根据 agent 类型选择执行路径：Alex 走工具链，其余角色走标准 LLM 流式输出
        if agent_name == 'Alex':
            return await self._run_alex_agent(context, stream_publisher)
        template = SYSTEM_PROMPTS.get(agent_name)
        prompt = template.format(user_message=context.user_message) if template else context.user_message
        provider = AGENT_PROVIDERS.get(agent_name, 'openai')
        message_id = self._new_message_id()
        # 非 Alex 角色统一走 LLM streaming，消费系统提示词
        result = await self._stream_llm_output(
            session_id=context.session_id,
            sender='agent',
            agent_name=agent_name,
            prompt=prompt,
            provider=provider,
            stream_publisher=stream_publisher,
            message_id=message_id,
        )
        return result, message_id

    async def _run_alex_agent(
        self, context: WorkflowContext, stream_publisher: Optional[StreamPublisher]
    ) -> tuple[str, str]:
        message_id = self._new_message_id()
        # Alex 需要访问工具，因此走独立 AgentContext + act 流程
        agent_context = AgentContext(
            session_id=context.session_id,
            user_id=context.user_id,
            owner_id=context.owner_id,
            user_message=context.user_message,
            tools=context.tools,
        )
        result = await self._alex_agent.act(agent_context)
        # act 结果不是流式返回，这里一次性推送 final token
        await self._publish_event(
            stream_publisher,
            context.session_id,
            {
                'type': 'token',
                'sender': 'agent',
                'agent': 'Alex',
                'content': result,
                'message_id': message_id,
                'final': True,
            },
        )
        return result, message_id

    async def _stream_llm_output(
        self,
        *,
        session_id: str,
        sender: SenderRole,
        agent_name: AgentRole,
        prompt: str,
        provider: str,
        stream_publisher: Optional[StreamPublisher],
        message_id: str,
        ) -> str:
        chunks: list[str] = []
        try:
            # 逐 chunk 消费 LLM 输出，并向前端推流 token
            async for chunk in self._llm_service.stream_generate(prompt=prompt, provider=provider):
                chunks.append(chunk)
                await self._publish_event(
                    stream_publisher,
                    session_id,
                    {
                        'type': 'token',
                        'sender': sender,
                        'agent': agent_name,
                        'content': chunk,
                        'message_id': message_id,
                        'final': False,
                    },
                )
            full_text = ''.join(chunks)
            # LLM 完成后补发 final=true 的聚合内容，方便前端落盘
            await self._publish_event(
                stream_publisher,
                session_id,
                {
                    'type': 'token',
                    'sender': sender,
                    'agent': agent_name,
                    'content': full_text,
                    'message_id': message_id,
                    'final': True,
                },
            )
            return full_text
        except LLMProviderError as exc:
            await self._publish_event(
                stream_publisher,
                session_id,
                {
                    'type': 'error',
                    'sender': 'status',
                    'agent': agent_name,
                    'content': str(exc),
                    'message_id': message_id,
                    'final': True,
                },
            )
            raise

    async def _emit_status(
        self,
        dispatches: list[AgentDispatch],
        session_id: str,
        content: str,
        stream_publisher: Optional[StreamPublisher],
    ) -> None:
        # status 消息既保存到 dispatches，也通过 WebSocket 广播提示
        message_id = self._new_message_id()
        dispatches.append(
            AgentDispatch(sender='status', agent='Mike', content=content, message_id=message_id)
        )
        await self._publish_event(
            stream_publisher,
            session_id,
            {
                'type': 'status',
                'sender': 'status',
                'agent': 'Mike',
                'content': content,
                'message_id': message_id,
                'final': True,
            },
        )

    async def _publish_event(
        self,
        publisher: Optional[StreamPublisher],
        session_id: str,
        payload: Dict[str, object],
    ) -> None:
        if not publisher:
            return
        # 统一为事件加上 session_id，方便前端在房间内路由
        event = {'session_id': session_id, **payload}
        await publisher(event)

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
