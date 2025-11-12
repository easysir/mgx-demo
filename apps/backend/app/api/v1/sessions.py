from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.models import Message, SessionCreate, SessionResponse, UserProfile
from app.services import session_repository, container_manager, SandboxError, file_watcher_manager

router = APIRouter()


@router.get("", response_model=list[SessionResponse])
async def list_sessions(user: UserProfile = Depends(get_current_user)) -> list[SessionResponse]:
    return session_repository.list_sessions(user.id)


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    payload: SessionCreate | None = None,
    user: UserProfile = Depends(get_current_user),
) -> SessionResponse:
    """Create a new chat session."""
    session = session_repository.create_session(owner_id=user.id, payload=payload)
    try:
        instance = container_manager.ensure_session_container(session_id=session.id, owner_id=user.id)
        file_watcher_manager.ensure_watch(session.id, instance.workspace_path)
    except SandboxError as exc:
        session_repository.delete_session(session.id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return session


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, user: UserProfile = Depends(get_current_user)) -> SessionResponse:
    session = session_repository.get_session(session_id, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/{session_id}/messages", response_model=list[Message])
async def list_messages(session_id: str, user: UserProfile = Depends(get_current_user)) -> list[Message]:
    session = session_repository.get_session(session_id, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.messages


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str, user: UserProfile = Depends(get_current_user)) -> None:
    session = session_repository.get_session(session_id, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    container_manager.destroy_session_container(session_id)
    file_watcher_manager.stop_watch(session_id)
    session_repository.delete_session(session_id)
