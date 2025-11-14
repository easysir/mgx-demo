"""Shared tool executor manager for agents and gateway."""

from __future__ import annotations

from typing import Optional, Callable, Awaitable, Dict, Any

from agents.tools import ToolExecutor, ToolAdapters, build_tool_executor
from agents.container.capabilities import (
    sandbox_file_capability,
    sandbox_command_capability,
)

ToolEventHook = Callable[[str, Dict[str, Any]], Awaitable[None]]

_executor: ToolExecutor | None = None
_event_hooks: list[ToolEventHook] = []


def register_event_hook(hook: ToolEventHook) -> None:
    if hook not in _event_hooks:
        _event_hooks.append(hook)


def _build_default_executor() -> ToolExecutor:
    adapters = ToolAdapters(
        sandbox_file=sandbox_file_capability,
        sandbox_command=sandbox_command_capability,
    )
    executor = build_tool_executor(adapters)
    executor.set_event_hook(_dispatch_event)
    return executor


async def _dispatch_event(tool_name: str, params: Dict[str, Any]) -> None:
    for hook in _event_hooks:
        await hook(tool_name, params)


def get_tool_executor() -> ToolExecutor:
    global _executor
    if _executor is None:
        _executor = _build_default_executor()
    return _executor


__all__ = ['get_tool_executor', 'register_event_hook', 'ToolEventHook']
