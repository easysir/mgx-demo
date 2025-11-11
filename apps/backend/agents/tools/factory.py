from __future__ import annotations

from dataclasses import dataclass

from .adapters import SandboxFileAdapter
from .executor import ToolExecutor
from .impl.file_write import FileWriteTool
from .impl.file_read import FileReadTool
from .impl.web_search import WebSearchTool


@dataclass(frozen=True)
class ToolAdapters:
    sandbox_file: SandboxFileAdapter


def build_tool_executor(adapters: ToolAdapters) -> ToolExecutor:
    executor = ToolExecutor()
    executor.register(FileWriteTool(adapters.sandbox_file))
    executor.register(FileReadTool(adapters.sandbox_file))
    executor.register(WebSearchTool())
    return executor


__all__ = ['ToolAdapters', 'build_tool_executor']
