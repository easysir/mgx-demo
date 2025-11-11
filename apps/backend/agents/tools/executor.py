"""Agent tool executor and base abstractions."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Dict, Optional


ToolParams = Dict[str, Any]
ToolPayload = Dict[str, Any]


class ToolExecutionError(RuntimeError):
    """Raised when a tool fails to execute."""


class Tool(ABC):
    """Base interface that all agent tools must implement."""

    name: str
    description: str

    @abstractmethod
    async def run(self, *, params: ToolParams) -> ToolPayload: ...


logger = logging.getLogger(__name__)


class ToolExecutor:
    """Dispatches registered tools (editor, terminal, git, etc.) for agents."""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}
        self._event_hook: Optional[Callable[[str, ToolParams], Awaitable[None]]] = None

    def register(self, tool: Tool) -> None:
        if not getattr(tool, 'name', None):
            raise ValueError('Tool must define a non-empty name')
        self._tools[tool.name] = tool

    def unregister(self, tool_name: str) -> None:
        self._tools.pop(tool_name, None)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def get(self, tool_name: str) -> Tool | None:
        return self._tools.get(tool_name)

    def set_event_hook(self, hook: Callable[[str, ToolParams], Awaitable[None]] | None) -> None:
        """Register a coroutine callback triggered before each tool execution."""

        self._event_hook = hook

    async def run(self, tool_name: str, *, params: ToolParams) -> ToolPayload:
        tool = self._tools.get(tool_name)
        if not tool:
            raise ToolExecutionError(f'未知工具: {tool_name}')
        try:
            if self._event_hook:
                try:
                    await self._event_hook(tool_name, params)
                except Exception as exc:  # pragma: no cover - defensive logging
                    logger.warning('Tool event hook failed for %s: %s', tool_name, exc)
            return await tool.run(params=params)
        except ToolExecutionError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            raise ToolExecutionError(f'{tool_name} 执行失败: {exc}') from exc
