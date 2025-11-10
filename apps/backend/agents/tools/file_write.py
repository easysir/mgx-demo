"""Agent-visible file writing tool."""

from __future__ import annotations

from typing import Any, Dict

from .adapters import SandboxFileAdapter
from .executor import Tool, ToolExecutionError


class FileWriteTool(Tool):
    name = "file_write"
    description = "写入或追加沙箱中的文件，并告知调度器具体路径。"

    def __init__(self, adapter: SandboxFileAdapter) -> None:
        self._adapter = adapter

    async def run(self, *, params: Dict[str, Any]) -> Dict[str, Any]:
        session_id = self._require_str(params, "session_id")
        owner_id = self._require_str(params, "owner_id")
        path = self._require_str(params, "path")
        content = params.get("content", "")
        if not isinstance(content, str):
            raise ToolExecutionError("content 必须为字符串")
        overwrite = bool(params.get("overwrite", True))
        append = bool(params.get("append", False))
        encoding = params.get("encoding") or "utf-8"

        try:
            result = await self._adapter.write_file(
                session_id=session_id,
                owner_id=owner_id,
                path=path,
                content=content,
                overwrite=overwrite,
                append=append,
                encoding=encoding,
            )
        except Exception as exc:  # pragma: no cover - adapter-specific errors
            raise ToolExecutionError(str(exc)) from exc
        return {
            "tool": self.name,
            **result,
        }

    def _require_str(self, params: Dict[str, Any], key: str) -> str:
        value = params.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ToolExecutionError(f"{key} 参数缺失或无效")
        return value.strip()
