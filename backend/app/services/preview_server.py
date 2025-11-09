import asyncio
import aiohttp
import os
from typing import Dict, Optional, Any
from pathlib import Path
from pydantic import BaseModel
import uuid


class PreviewConfig(BaseModel):
    """预览服务器配置"""
    port: int = 3000
    host: str = "localhost"
    auto_reload: bool = True
    build_command: Optional[str] = None
    dev_command: Optional[str] = None


class PreviewStatus(BaseModel):
    """预览状态"""
    session_id: str
    status: str  # starting, running, stopped, error
    url: Optional[str] = None
    port: Optional[int] = None
    error: Optional[str] = None


class PreviewServer:
    """
    预览服务器
    为每个会话提供独立的预览环境
    """
    
    def __init__(
        self,
        session_id: str,
        working_dir: Path,
        config: Optional[PreviewConfig] = None
    ):
        self.session_id = session_id
        self.working_dir = working_dir
        self.config = config or PreviewConfig()
        self.process: Optional[asyncio.subprocess.Process] = None
        self.status = "stopped"
        self.port: Optional[int] = None
        self.url: Optional[str] = None
    
    async def start(
        self,
        command: Optional[str] = None,
        port: Optional[int] = None
    ) -> PreviewStatus:
        """
        启动预览服务器
        
        Args:
            command: 启动命令(如果为None,则自动检测)
            port: 端口号(如果为None,则自动分配)
            
        Returns:
            PreviewStatus: 预览状态
        """
        try:
            self.status = "starting"
            
            # 确定端口
            if port:
                self.port = port
            else:
                self.port = await self._find_available_port()
            
            # 确定启动命令
            if not command:
                command = await self._detect_dev_command()
            
            if not command:
                self.status = "error"
                return PreviewStatus(
                    session_id=self.session_id,
                    status="error",
                    error="No dev command found. Please specify a command or ensure package.json exists."
                )
            
            # 启动开发服务器
            cmd_parts = command.split()
            
            self.process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.working_dir),
                env={
                    **dict(os.environ),
                    "PORT": str(self.port)
                }
            )
            
            # 等待服务器启动
            await self._wait_for_server_ready()
            
            self.status = "running"
            self.url = f"http://{self.config.host}:{self.port}"
            
            return PreviewStatus(
                session_id=self.session_id,
                status="running",
                url=self.url,
                port=self.port
            )
            
        except Exception as e:
            self.status = "error"
            return PreviewStatus(
                session_id=self.session_id,
                status="error",
                error=str(e)
            )
    
    async def stop(self) -> PreviewStatus:
        """
        停止预览服务器
        
        Returns:
            PreviewStatus: 预览状态
        """
        try:
            if self.process:
                self.process.kill()
                await self.process.wait()
                self.process = None
            
            self.status = "stopped"
            self.url = None
            
            return PreviewStatus(
                session_id=self.session_id,
                status="stopped"
            )
        except Exception as e:
            return PreviewStatus(
                session_id=self.session_id,
                status="error",
                error=str(e)
            )
    
    def get_status(self) -> PreviewStatus:
        """
        获取预览状态
        
        Returns:
            PreviewStatus: 当前状态
        """
        return PreviewStatus(
            session_id=self.session_id,
            status=self.status,
            url=self.url,
            port=self.port
        )
    
    async def _detect_dev_command(self) -> Optional[str]:
        """
        自动检测开发命令
        
        Returns:
            Optional[str]: 开发命令
        """
        # 检查package.json
        package_json = self.working_dir / "package.json"
        if package_json.exists():
            try:
                import json
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    scripts = data.get('scripts', {})
                    
                    # 优先级: dev > start > serve
                    if 'dev' in scripts:
                        return "npm run dev"
                    elif 'start' in scripts:
                        return "npm start"
                    elif 'serve' in scripts:
                        return "npm run serve"
            except Exception:
                pass
        
        # 检查index.html(静态网站)
        index_html = self.working_dir / "index.html"
        if index_html.exists():
            return "python3 -m http.server"
        
        return None
    
    async def _find_available_port(self, start_port: int = 3000) -> int:
        """
        查找可用端口
        
        Args:
            start_port: 起始端口
            
        Returns:
            int: 可用端口
        """
        import socket
        
        port = start_port
        while port < start_port + 100:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('', port))
                sock.close()
                return port
            except OSError:
                port += 1
        
        raise RuntimeError("No available port found")
    
    async def _wait_for_server_ready(self, timeout: int = 30):
        """
        等待服务器就绪
        
        Args:
            timeout: 超时时间(秒)
        """
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://{self.config.host}:{self.port}") as response:
                        if response.status < 500:
                            return
            except Exception:
                pass
            
            await asyncio.sleep(1)
        
        raise TimeoutError(f"Server did not start within {timeout} seconds")


class PreviewManager:
    """
    预览管理器
    管理所有会话的预览服务器
    """
    
    def __init__(self):
        self.servers: Dict[str, PreviewServer] = {}
    
    def get_or_create_server(
        self,
        session_id: str,
        working_dir: Path,
        config: Optional[PreviewConfig] = None
    ) -> PreviewServer:
        """
        获取或创建预览服务器
        
        Args:
            session_id: 会话ID
            working_dir: 工作目录
            config: 预览配置
            
        Returns:
            PreviewServer: 预览服务器实例
        """
        if session_id not in self.servers:
            self.servers[session_id] = PreviewServer(
                session_id=session_id,
                working_dir=working_dir,
                config=config
            )
        
        return self.servers[session_id]
    
    async def stop_server(self, session_id: str) -> PreviewStatus:
        """
        停止预览服务器
        
        Args:
            session_id: 会话ID
            
        Returns:
            PreviewStatus: 预览状态
        """
        if session_id in self.servers:
            status = await self.servers[session_id].stop()
            del self.servers[session_id]
            return status
        
        return PreviewStatus(
            session_id=session_id,
            status="stopped"
        )
    
    async def stop_all(self):
        """停止所有预览服务器"""
        for session_id in list(self.servers.keys()):
            await self.stop_server(session_id)


# 全局预览管理器实例
preview_manager = PreviewManager()