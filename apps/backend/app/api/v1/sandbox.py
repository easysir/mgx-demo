from __future__ import annotations

import subprocess

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies.auth import get_current_user
from app.models import SessionCreate, SessionResponse, UserProfile
from app.services import (
    container_manager,
    session_repository,
    SandboxError,
    file_watcher_manager,
    sandbox_command_service,
)


class SandboxLaunchRequest(BaseModel):
    session_id: str | None = None
    title: str | None = None


class SandboxLaunchResponse(BaseModel):
    session: SessionResponse
    container_id: str
    container_name: str
    workspace_path: str
    logs: list[str]


class SandboxDestroyRequest(BaseModel):
    session_id: str


class SandboxDestroyResponse(BaseModel):
    session_id: str
    stopped: bool


class SandboxDestroyAllResponse(BaseModel):
    stopped_sessions: list[str]


class SandboxExecRequest(BaseModel):
    session_id: str
    command: str
    cwd: str | None = None
    env: dict[str, str] | None = None
    timeout: int | None = None


class SandboxExecResponse(BaseModel):
    command: str
    exit_code: int
    stdout: str
    stderr: str


class SandboxPreviewTarget(BaseModel):
    container_port: int
    host_port: int
    url: str


class SandboxPreviewResponse(BaseModel):
    session_id: str
    available: bool
    previews: list[SandboxPreviewTarget]


router = APIRouter()


@router.post("/launch", response_model=SandboxLaunchResponse, status_code=201)
async def launch_sandbox(
    payload: SandboxLaunchRequest | None = None,
    user: UserProfile = Depends(get_current_user),
) -> SandboxLaunchResponse:
    logs: list[str] = []

    session = None
    if payload and payload.session_id:
        session = session_repository.get_session(payload.session_id, user.id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        logs.append(f"复用会话 {session.id}")
    else:
        session = session_repository.create_session(owner_id=user.id, payload=SessionCreate(title=payload.title if payload else None))
        logs.append(f"创建新会话 {session.id}")

    session_response = SessionResponse(**session.model_dump())

    try:
        instance = container_manager.ensure_session_container(session_id=session.id, owner_id=user.id)
        file_watcher_manager.ensure_watch(session.id, instance.workspace_path)
        logs.append(f"容器 {instance.container_name} 已启动（ID: {instance.container_id}）")
        logs.append(f"工作目录: {instance.workspace_path}")
    except SandboxError as exc:
        logs.append(f"容器启动失败: {exc}")
        if not payload or not payload.session_id:
            session_repository.delete_session(session.id)
        raise HTTPException(status_code=500, detail=str(exc))

    return SandboxLaunchResponse(
        session=session_response,
        container_id=instance.container_id,
        container_name=instance.container_name,
        workspace_path=str(instance.workspace_path),
        logs=logs,
    )


@router.post("/destroy", response_model=SandboxDestroyResponse)
async def destroy_sandbox(
    payload: SandboxDestroyRequest,
    user: UserProfile = Depends(get_current_user),
) -> SandboxDestroyResponse:
    session = session_repository.get_session(payload.session_id, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    stopped = container_manager.destroy_session_container(payload.session_id)
    if stopped:
        file_watcher_manager.stop_watch(payload.session_id)
    return SandboxDestroyResponse(session_id=payload.session_id, stopped=stopped)


@router.post("/destroy_all", response_model=SandboxDestroyAllResponse)
async def destroy_all_sandboxes(user: UserProfile = Depends(get_current_user)) -> SandboxDestroyAllResponse:
    stopped_sessions = container_manager.destroy_all(owner_id=user.id)
    for session_id in stopped_sessions:
        file_watcher_manager.stop_watch(session_id)
    return SandboxDestroyAllResponse(stopped_sessions=stopped_sessions)


@router.post("/exec", response_model=SandboxExecResponse)
async def exec_in_sandbox(
    payload: SandboxExecRequest,
    user: UserProfile = Depends(get_current_user),
) -> SandboxExecResponse:
    session = session_repository.get_session(payload.session_id, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        result = await sandbox_command_service.run_command(
            session_id=payload.session_id,
            owner_id=session.owner_id,
            command=payload.command,
            cwd=payload.cwd,
            env=payload.env,
            timeout=payload.timeout or 300,
        )
        return SandboxExecResponse(
            command=result.command,
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    except SandboxError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except subprocess.TimeoutExpired as exc:  # type: ignore[name-defined]
        raise HTTPException(status_code=408, detail="Command execution timed out") from exc


@router.get("/preview/{session_id}", response_model=SandboxPreviewResponse)
async def sandbox_preview(
    session_id: str,
    user: UserProfile = Depends(get_current_user),
) -> SandboxPreviewResponse:
    session = session_repository.get_session(session_id, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        instance = container_manager.ensure_session_container(session_id=session.id, owner_id=session.owner_id)
        file_watcher_manager.ensure_watch(session.id, instance.workspace_path)
    except SandboxError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    previews: list[SandboxPreviewTarget] = []
    base_url = container_manager.config.preview_host.rstrip("/")
    for container_port, host_port in sorted(instance.port_map.items()):
        if not host_port:
            continue
        url = f"{base_url}:{host_port}"
        previews.append(
            SandboxPreviewTarget(
                container_port=container_port,
                host_port=host_port,
                url=url,
            )
        )
    return SandboxPreviewResponse(session_id=session.id, available=bool(previews), previews=previews)
