from __future__ import annotations

from typing import Any, Dict

from ..adapters import SandboxFileAdapter
from ..executor import Tool, ToolExecutionError


class FileReadTool(Tool):
    name = 'file_read'
    description = '读取沙箱中的文件内容，供 Agent 查看已有实现。'

    def __init__(self, adapter: SandboxFileAdapter) -> None:
        self._adapter = adapter

    async def run(self, *, params: Dict[str, Any]) -> Dict[str, Any]:
        session_id = self._require_str(params, 'session_id')
        owner_id = self._require_str(params, 'owner_id')
        path = self._require_str(params, 'path')
        try:
            result = await self._adapter.read_file(
                session_id=session_id,
                owner_id=owner_id,
                path=path,
            )
        except Exception as exc:  # pragma: no cover - adapter-specific errors
            raise ToolExecutionError(str(exc)) from exc
        return {
            'tool': self.name,
            **result,
        }

    def _require_str(self, params: Dict[str, Any], key: str) -> str:
        value = params.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ToolExecutionError(f"{key} 参数缺失或无效")
        return value.strip()
