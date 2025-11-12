from __future__ import annotations

from typing import Any, Dict, Optional

from ..adapters import SandboxCommandAdapter
from ..executor import Tool, ToolExecutionError


class SandboxShellTool(Tool):
    name = "sandbox_shell"
    description = "在沙箱容器内执行 shell 命令，可选择工作目录与环境变量。"

    def __init__(self, adapter: SandboxCommandAdapter) -> None:
        self._adapter = adapter

    async def run(self, *, params: Dict[str, Any]) -> Dict[str, Any]:
        session_id = self._require_str(params, "session_id")
        owner_id = self._require_str(params, "owner_id")
        command = self._require_str(params, "command")
        cwd = self._optional_str(params.get("cwd"))
        env = self._optional_env(params.get("env"))
        timeout = self._optional_timeout(params.get("timeout"))

        result = await self._adapter.run_command(
            session_id=session_id,
            owner_id=owner_id,
            command=command,
            cwd=cwd,
            env=env,
            timeout=timeout,
        )
        return {
            "tool": self.name,
            **result,
        }

    def _require_str(self, params: Dict[str, Any], key: str | None = None) -> str:
        if key is None:
            raise ToolExecutionError("Internal error: missing key")
        value = params.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ToolExecutionError(f"{key} 参数缺失或无效")
        return value.strip()

    def _optional_str(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ToolExecutionError("cwd 必须是字符串")
        trimmed = value.strip()
        return trimmed or None

    def _optional_env(self, value: Any) -> Optional[Dict[str, str]]:
        if value is None:
            return None
        if not isinstance(value, dict):
            raise ToolExecutionError("env 必须是对象")
        env: Dict[str, str] = {}
        for key, val in value.items():
            if not isinstance(key, str):
                raise ToolExecutionError("env 键必须是字符串")
            if not isinstance(val, str):
                raise ToolExecutionError("env 值必须是字符串")
            env[key] = val
        return env

    def _optional_timeout(self, value: Any) -> int:
        if value is None:
            return 300
        if isinstance(value, int) and value > 0:
            return value
        raise ToolExecutionError("timeout 必须是正整数")
