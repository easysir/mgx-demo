from __future__ import annotations

from dataclasses import dataclass

from .adapters import SandboxFileAdapter
from .executor import ToolExecutor
from .file_write import FileWriteTool


@dataclass(frozen=True)
class ToolAdapters:
    sandbox_file: SandboxFileAdapter


def build_tool_executor(adapters: ToolAdapters) -> ToolExecutor:
    executor = ToolExecutor()
    executor.register(FileWriteTool(adapters.sandbox_file))
    return executor


__all__ = ['ToolAdapters', 'build_tool_executor']
