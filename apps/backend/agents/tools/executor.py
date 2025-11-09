"""Shared tool executor placeholder."""

from __future__ import annotations

from typing import Any, Dict


class ToolExecutor:
    """Dispatches tool calls (editor, terminal, git, etc.) for agents.

    TODO: Replace with real implementations once Phase 2 工具链接入完成。
    """

    async def run(self, tool_name: str, *, params: Dict[str, Any]) -> Dict[str, Any]:
        return {'tool': tool_name, 'status': 'not-implemented', 'params': params}
