import os
import aiofiles
from typing import Dict, Any
from pathlib import Path

from app.tools.base import Tool, ToolResult


class FileSystemTool(Tool):
    """
    文件系统工具,用于读写文件
    """
    
    def __init__(self, base_directory: str = "/workspace/user_sessions"):
        super().__init__()
        self.base_directory = Path(base_directory)
        self.description = "Read and write files in the session's working directory"
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        """
        执行文件操作
        
        支持的操作:
        - read: 读取文件内容
        - write: 写入文件内容
        - list: 列出目录内容
        
        Args:
            params: {
                "operation": "read" | "write" | "list",
                "path": "file_path",
                "content": "file_content" (仅write操作需要)
            }
        """
        import time
        start_time = time.time()
        
        try:
            operation = params.get("operation")
            relative_path = params.get("path", "")
            
            # 构建完整路径并确保在base_directory内
            full_path = (self.base_directory / relative_path).resolve()
            
            # 安全检查:确保路径在base_directory内
            if not str(full_path).startswith(str(self.base_directory)):
                return ToolResult(
                    success=False,
                    error="Access denied: path is outside working directory",
                    execution_time=time.time() - start_time
                )
            
            if operation == "read":
                return await self._read_file(full_path, start_time)
            elif operation == "write":
                content = params.get("content", "")
                return await self._write_file(full_path, content, start_time)
            elif operation == "list":
                return await self._list_directory(full_path, start_time)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown operation: {operation}",
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def _read_file(self, path: Path, start_time: float) -> ToolResult:
        """读取文件内容"""
        try:
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            return ToolResult(
                success=True,
                output=content,
                execution_time=time.time() - start_time
            )
        except FileNotFoundError:
            return ToolResult(
                success=False,
                error=f"File not found: {path}",
                execution_time=time.time() - start_time
            )
    
    async def _write_file(self, path: Path, content: str, start_time: float) -> ToolResult:
        """写入文件内容"""
        try:
            # 确保目录存在
            path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            return ToolResult(
                success=True,
                output=f"File written successfully: {path}",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to write file: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    async def _list_directory(self, path: Path, start_time: float) -> ToolResult:
        """列出目录内容"""
        try:
            if not path.exists():
                return ToolResult(
                    success=False,
                    error=f"Directory not found: {path}",
                    execution_time=time.time() - start_time
                )
            
            if not path.is_dir():
                return ToolResult(
                    success=False,
                    error=f"Path is not a directory: {path}",
                    execution_time=time.time() - start_time
                )
            
            items = []
            for item in path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            
            return ToolResult(
                success=True,
                output=items,
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to list directory: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证参数"""
        operation = params.get("operation")
        if operation not in ["read", "write", "list"]:
            return False
        
        if "path" not in params:
            return False
        
        if operation == "write" and "content" not in params:
            return False
        
        return True