"""Base class shared by all agents.

这个模块定义了 Agent 在运行时的标准接口，确保每个角色都能以一致的方式接收上下文、规划任务并输出结果。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from shared.types import AgentRole

from ..tools import ToolExecutor


@dataclass
class AgentContext:
    """Runtime context injected into each agent.

    运行时上下文会携带会话、用户和当前输入等信息，方便 Agent 在不共享状态的情况下读取所需数据。
    """

    session_id: str
    user_id: str
    owner_id: str
    user_message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    tools: Optional[ToolExecutor] = None


class BaseAgent:
    """Base behaviour that concrete agents can extend.

    基类约定了 plan/act/report 生命周期，具体角色可按需覆写，从而保持协作流程统一。
    """

    name: AgentRole

    def __init__(self, *, name: AgentRole, description: str) -> None:
        self.name = name
        self.description = description

    async def plan(self, context: AgentContext) -> str:
        """Optional planning step before执行工具。"""
        raise NotImplementedError

    async def act(self, context: AgentContext) -> str:
        """Execute核心逻辑，例如调用LLM或工具。"""
        raise NotImplementedError

    async def report(self, context: AgentContext, result: str) -> str:
        """整理输出给 Mike/用户。"""
        return result
