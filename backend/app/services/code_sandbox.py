import asyncio
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
import uuid
import time
import psutil
from pydantic import BaseModel


class ExecutionResult(BaseModel):
    """代码执行结果"""
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    execution_time: float = 0.0
    error: Optional[str] = None


class SandboxConfig(BaseModel):
    """沙箱配置"""
    max_execution_time: int = 30  # 最大执行时间(秒)
    max_memory_mb: int = 512  # 最大内存(MB)
    max_cpu_percent: float = 50.0  # 最大CPU使用率(%)
    allowed_commands: List[str] = ["node", "npm", "python", "python3", "pip", "pip3"]


class CodeSandbox:
    """
    代码沙箱服务
    提供隔离的代码执行环境
    """
    
    def __init__(
        self,
        session_id: str,
        base_directory: str = "/workspace/user_sessions",
        config: Optional[SandboxConfig] = None
    ):
        self.session_id = session_id
        self.base_directory = Path(base_directory)
        self.working_dir = self.base_directory / session_id
        self.config = config or SandboxConfig()
        self.processes: Dict[str, asyncio.subprocess.Process] = {}
        
        # 确保工作目录存在
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"CodeSandbox initialized for session {session_id}")
        print(f"Working directory: {self.working_dir}")
    
    async def execute_code(
        self,
        code: str,
        language: str = "python",
        filename: Optional[str] = None
    ) -> ExecutionResult:
        """
        执行代码
        
        Args:
            code: 要执行的代码
            language: 编程语言 (python, javascript, typescript)
            filename: 文件名(可选)
            
        Returns:
            ExecutionResult: 执行结果
        """
        start_time = time.time()
        
        try:
            # 创建临时文件
            if not filename:
                if language == "python":
                    filename = f"temp_{uuid.uuid4().hex[:8]}.py"
                elif language in ["javascript", "typescript"]:
                    filename = f"temp_{uuid.uuid4().hex[:8]}.js"
                else:
                    return ExecutionResult(
                        exit_code=1,
                        error=f"Unsupported language: {language}"
                    )
            
            file_path = self.working_dir / filename
            
            # 写入代码到文件
            async with asyncio.Lock():
                file_path.write_text(code, encoding='utf-8')
            
            # 根据语言选择执行命令
            if language == "python":
                cmd = ["python3", str(file_path)]
            elif language == "javascript":
                cmd = ["node", str(file_path)]
            elif language == "typescript":
                # TypeScript需要先编译
                cmd = ["npx", "ts-node", str(file_path)]
            else:
                return ExecutionResult(
                    exit_code=1,
                    error=f"Unsupported language: {language}"
                )
            
            # 执行命令
            result = await self._run_command(
                cmd,
                timeout=self.config.max_execution_time
            )
            
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            return result
            
        except Exception as e:
            return ExecutionResult(
                exit_code=1,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def execute_command(
        self,
        command: str,
        args: List[str] = None,
        timeout: Optional[int] = None
    ) -> ExecutionResult:
        """
        执行系统命令
        
        Args:
            command: 命令名称
            args: 命令参数
            timeout: 超时时间(秒)
            
        Returns:
            ExecutionResult: 执行结果
        """
        # 安全检查:只允许白名单中的命令
        if command not in self.config.allowed_commands:
            return ExecutionResult(
                exit_code=1,
                error=f"Command not allowed: {command}"
            )
        
        cmd = [command] + (args or [])
        timeout = timeout or self.config.max_execution_time
        
        return await self._run_command(cmd, timeout=timeout)
    
    async def _run_command(
        self,
        cmd: List[str],
        timeout: int = 30
    ) -> ExecutionResult:
        """
        运行命令(内部方法)
        
        Args:
            cmd: 命令列表
            timeout: 超时时间(秒)
            
        Returns:
            ExecutionResult: 执行结果
        """
        start_time = time.time()
        
        try:
            # 创建子进程
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.working_dir)
            )
            
            # 等待进程完成(带超时)
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                return ExecutionResult(
                    stdout=stdout.decode('utf-8', errors='replace'),
                    stderr=stderr.decode('utf-8', errors='replace'),
                    exit_code=process.returncode,
                    execution_time=time.time() - start_time
                )
                
            except asyncio.TimeoutError:
                # 超时,终止进程
                process.kill()
                await process.wait()
                
                return ExecutionResult(
                    exit_code=-1,
                    error=f"Execution timeout after {timeout} seconds",
                    execution_time=time.time() - start_time
                )
                
        except Exception as e:
            return ExecutionResult(
                exit_code=1,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def install_dependencies(
        self,
        package_manager: str = "npm",
        packages: Optional[List[str]] = None
    ) -> ExecutionResult:
        """
        安装依赖包
        
        Args:
            package_manager: 包管理器 (npm, pip)
            packages: 要安装的包列表(可选,如果为None则安装package.json或requirements.txt中的依赖)
            
        Returns:
            ExecutionResult: 执行结果
        """
        if package_manager == "npm":
            if packages:
                cmd = ["npm", "install"] + packages
            else:
                cmd = ["npm", "install"]
        elif package_manager == "pip":
            if packages:
                cmd = ["pip3", "install"] + packages
            else:
                cmd = ["pip3", "install", "-r", "requirements.txt"]
        else:
            return ExecutionResult(
                exit_code=1,
                error=f"Unsupported package manager: {package_manager}"
            )
        
        return await self._run_command(cmd, timeout=300)  # 5分钟超时
    
    async def create_file(self, path: str, content: str) -> bool:
        """
        创建或更新文件
        
        Args:
            path: 文件路径(相对于工作目录)
            content: 文件内容
            
        Returns:
            bool: 是否成功
        """
        try:
            file_path = self.working_dir / path
            
            # 确保父目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            file_path.write_text(content, encoding='utf-8')
            
            return True
        except Exception as e:
            print(f"Failed to create file {path}: {e}")
            return False
    
    async def read_file(self, path: str) -> Optional[str]:
        """
        读取文件内容
        
        Args:
            path: 文件路径(相对于工作目录)
            
        Returns:
            Optional[str]: 文件内容,如果失败则返回None
        """
        try:
            file_path = self.working_dir / path
            
            if not file_path.exists():
                return None
            
            return file_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Failed to read file {path}: {e}")
            return None
    
    async def delete_file(self, path: str) -> bool:
        """
        删除文件
        
        Args:
            path: 文件路径(相对于工作目录)
            
        Returns:
            bool: 是否成功
        """
        try:
            file_path = self.working_dir / path
            
            if file_path.exists():
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
                
            return True
        except Exception as e:
            print(f"Failed to delete file {path}: {e}")
            return False
    
    async def list_files(self, path: str = ".") -> List[Dict[str, Any]]:
        """
        列出目录内容
        
        Args:
            path: 目录路径(相对于工作目录)
            
        Returns:
            List[Dict]: 文件列表
        """
        try:
            dir_path = self.working_dir / path
            
            if not dir_path.exists() or not dir_path.is_dir():
                return []
            
            files = []
            for item in dir_path.iterdir():
                files.append({
                    "name": item.name,
                    "path": str(item.relative_to(self.working_dir)),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            
            return files
        except Exception as e:
            print(f"Failed to list files in {path}: {e}")
            return []
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """
        获取资源使用情况
        
        Returns:
            Dict: 资源使用信息
        """
        try:
            # 获取当前进程的资源使用
            process = psutil.Process()
            
            return {
                "cpu_percent": process.cpu_percent(interval=0.1),
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "num_threads": process.num_threads(),
                "working_dir_size_mb": self._get_directory_size(self.working_dir) / 1024 / 1024
            }
        except Exception as e:
            print(f"Failed to get resource usage: {e}")
            return {}
    
    def _get_directory_size(self, path: Path) -> int:
        """获取目录大小(字节)"""
        total_size = 0
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
        except Exception:
            pass
        return total_size
    
    async def cleanup(self):
        """
        清理沙箱环境
        """
        try:
            # 终止所有进程
            for process_id, process in self.processes.items():
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass
            
            self.processes.clear()
            
            # 可选:删除工作目录(谨慎使用)
            # if self.working_dir.exists():
            #     shutil.rmtree(self.working_dir)
            
            print(f"CodeSandbox cleaned up for session {self.session_id}")
        except Exception as e:
            print(f"Failed to cleanup sandbox: {e}")


class SandboxManager:
    """
    沙箱管理器
    管理所有会话的沙箱实例
    """
    
    def __init__(self):
        self.sandboxes: Dict[str, CodeSandbox] = {}
    
    def get_or_create_sandbox(
        self,
        session_id: str,
        config: Optional[SandboxConfig] = None
    ) -> CodeSandbox:
        """
        获取或创建沙箱实例
        
        Args:
            session_id: 会话ID
            config: 沙箱配置
            
        Returns:
            CodeSandbox: 沙箱实例
        """
        if session_id not in self.sandboxes:
            self.sandboxes[session_id] = CodeSandbox(
                session_id=session_id,
                config=config
            )
        
        return self.sandboxes[session_id]
    
    async def cleanup_sandbox(self, session_id: str):
        """
        清理指定会话的沙箱
        
        Args:
            session_id: 会话ID
        """
        if session_id in self.sandboxes:
            await self.sandboxes[session_id].cleanup()
            del self.sandboxes[session_id]
    
    async def cleanup_all(self):
        """清理所有沙箱"""
        for session_id in list(self.sandboxes.keys()):
            await self.cleanup_sandbox(session_id)


# 全局沙箱管理器实例
sandbox_manager = SandboxManager()