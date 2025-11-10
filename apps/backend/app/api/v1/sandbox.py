from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies.auth import get_current_user
from app.models import SessionCreate, SessionResponse, UserProfile
from app.services import container_manager, session_repository, SandboxError, file_watcher_manager


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
