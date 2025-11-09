"""Base class shared by all agents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from shared.types import AgentRole


@dataclass
class AgentContext:
    """Runtime context injected into each agent."""

    session_id: str
    user_id: str
    user_message: str
    metadata: Dict[str, Any]


class BaseAgent:
    """Base behaviour that concrete agents can extend."""

    name: AgentRole

    def __init__(self, *, name: AgentRole, description: str) -> None:
        self.name = name
        self.description = description

    async def plan(self, context: AgentContext) -> str:
        """Optional planning step before执行工具."""
        raise NotImplementedError

    async def act(self, context: AgentContext) -> str:
        """Execute核心逻辑，例如调用LLM或工具。"""
        raise NotImplementedError

    async def report(self, context: AgentContext, result: str) -> str:
        """整理输出给 Mike/用户。"""
        return result
