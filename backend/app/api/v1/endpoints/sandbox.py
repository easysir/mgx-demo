from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.services.code_sandbox import (
    sandbox_manager,
    ExecutionResult,
    SandboxConfig
)
from app.services.preview_server import (
    preview_manager,
    PreviewStatus,
    PreviewConfig
)
from app.services.session_manager import SessionManager
from app.dependencies import get_session_manager
from pathlib import Path

router = APIRouter()


class ExecuteCodeRequest(BaseModel):
    """执行代码请求"""
    session_id: str
    code: str
    language: str = "python"
    filename: Optional[str] = None


class ExecuteCommandRequest(BaseModel):
    """执行命令请求"""
    session_id: str
    command: str
    args: Optional[List[str]] = None
    timeout: Optional[int] = None


class FileOperationRequest(BaseModel):
    """文件操作请求"""
    session_id: str
    path: str
    content: Optional[str] = None


class InstallDependenciesRequest(BaseModel):
    """安装依赖请求"""
    session_id: str
    package_manager: str = "npm"
    packages: Optional[List[str]] = None


class StartPreviewRequest(BaseModel):
    """启动预览请求"""
    session_id: str
    command: Optional[str] = None
    port: Optional[int] = None


@router.post("/sandbox/execute", response_model=ExecutionResult)
async def execute_code(
    request: ExecuteCodeRequest,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    执行代码
    
    支持的语言:
    - python
    - javascript
    - typescript
    """
    # 验证会话
    session = await session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 获取沙箱
    sandbox = sandbox_manager.get_or_create_sandbox(request.session_id)
    
    # 执行代码
    result = await sandbox.execute_code(
        code=request.code,
        language=request.language,
        filename=request.filename
    )
    
    return result


@router.post("/sandbox/command", response_model=ExecutionResult)
async def execute_command(
    request: ExecuteCommandRequest,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    执行系统命令
    
    允许的命令:
    - node, npm
    - python, python3, pip, pip3
    """
    # 验证会话
    session = await session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 获取沙箱
    sandbox = sandbox_manager.get_or_create_sandbox(request.session_id)
    
    # 执行命令
    result = await sandbox.execute_command(
        command=request.command,
        args=request.args,
        timeout=request.timeout
    )
    
    return result


@router.post("/sandbox/install")
async def install_dependencies(
    request: InstallDependenciesRequest,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    安装依赖包
    
    支持的包管理器:
    - npm
    - pip
    """
    # 验证会话
    session = await session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 获取沙箱
    sandbox = sandbox_manager.get_or_create_sandbox(request.session_id)
    
    # 安装依赖
    result = await sandbox.install_dependencies(
        package_manager=request.package_manager,
        packages=request.packages
    )
    
    return result


@router.post("/sandbox/files")
async def create_or_update_file(
    request: FileOperationRequest,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """创建或更新文件"""
    if not request.content:
        raise HTTPException(status_code=400, detail="Content is required")
    
    # 验证会话
    session = await session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 获取沙箱
    sandbox = sandbox_manager.get_or_create_sandbox(request.session_id)
    
    # 创建文件
    success = await sandbox.create_file(request.path, request.content)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create file")
    
    return {"success": True, "path": request.path}


@router.get("/sandbox/files/{session_id}/{path:path}")
async def read_file(
    session_id: str,
    path: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """读取文件内容"""
    # 验证会话
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 获取沙箱
    sandbox = sandbox_manager.get_or_create_sandbox(session_id)
    
    # 读取文件
    content = await sandbox.read_file(path)
    
    if content is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {"path": path, "content": content}


@router.delete("/sandbox/files")
async def delete_file(
    request: FileOperationRequest,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """删除文件"""
    # 验证会话
    session = await session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 获取沙箱
    sandbox = sandbox_manager.get_or_create_sandbox(request.session_id)
    
    # 删除文件
    success = await sandbox.delete_file(request.path)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete file")
    
    return {"success": True, "path": request.path}


@router.get("/sandbox/files/{session_id}")
async def list_files(
    session_id: str,
    path: str = ".",
    session_manager: SessionManager = Depends(get_session_manager)
):
    """列出目录内容"""
    # 验证会话
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 获取沙箱
    sandbox = sandbox_manager.get_or_create_sandbox(session_id)
    
    # 列出文件
    files = await sandbox.list_files(path)
    
    return {"files": files}


@router.get("/sandbox/resources/{session_id}")
async def get_resource_usage(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """获取资源使用情况"""
    # 验证会话
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 获取沙箱
    sandbox = sandbox_manager.get_or_create_sandbox(session_id)
    
    # 获取资源使用
    usage = sandbox.get_resource_usage()
    
    return usage


@router.post("/preview/start", response_model=PreviewStatus)
async def start_preview(
    request: StartPreviewRequest,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """启动预览服务器"""
    # 验证会话
    session = await session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 获取工作目录
    sandbox = sandbox_manager.get_or_create_sandbox(request.session_id)
    working_dir = sandbox.working_dir
    
    # 获取预览服务器
    server = preview_manager.get_or_create_server(
        session_id=request.session_id,
        working_dir=working_dir
    )
    
    # 启动服务器
    status = await server.start(
        command=request.command,
        port=request.port
    )
    
    return status


@router.post("/preview/stop", response_model=PreviewStatus)
async def stop_preview(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """停止预览服务器"""
    # 验证会话
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 停止服务器
    status = await preview_manager.stop_server(session_id)
    
    return status


@router.get("/preview/status/{session_id}", response_model=PreviewStatus)
async def get_preview_status(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """获取预览状态"""
    # 验证会话
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 获取服务器状态
    if session_id in preview_manager.servers:
        server = preview_manager.servers[session_id]
        return server.get_status()
    
    return PreviewStatus(
        session_id=session_id,
        status="stopped"
    )


@router.delete("/sandbox/cleanup/{session_id}")
async def cleanup_sandbox(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """清理沙箱环境"""
    # 验证会话
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 停止预览服务器
    await preview_manager.stop_server(session_id)
    
    # 清理沙箱
    await sandbox_manager.cleanup_sandbox(session_id)
    
    return {"success": True, "message": "Sandbox cleaned up"}