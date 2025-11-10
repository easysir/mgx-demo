from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.dependencies.auth import get_current_user
from app.models import UserProfile
from app.services import file_service, FileAccessError, session_store


class FileNode(BaseModel):
    name: str
    path: str
    type: str = Field(pattern='^(file|directory)$')
    size: int
    children: list['FileNode'] | None = None


FileNode.model_rebuild()


class FileTreeResponse(BaseModel):
    root: str
    entries: list[FileNode]


class FileContentResponse(BaseModel):
    name: str
    path: str
    size: int
    modified_at: float
    content: str


router = APIRouter()


def _ensure_session(session_id: str, user: UserProfile):
    session = session_store.get_session(session_id, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get('/{session_id}/tree', response_model=FileTreeResponse)
async def list_tree(
    session_id: str,
    root: str = Query('', description='相对于项目根目录的路径'),
    depth: int = Query(2, ge=1, le=10),
    include_hidden: bool = Query(False),
    user: UserProfile = Depends(get_current_user),
) -> FileTreeResponse:
    _ensure_session(session_id, user)
    try:
        entries = file_service.list_tree(
            session_id=session_id,
            owner_id=user.id,
            root=root,
            depth=depth,
            include_hidden=include_hidden,
        )
    except FileAccessError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="指定路径不存在")

    return FileTreeResponse(root=root or '/', entries=entries)


@router.get('/{session_id}', response_model=FileContentResponse)
async def read_file(
    session_id: str,
    path: str = Query(..., description='相对项目根目录的文件路径'),
    user: UserProfile = Depends(get_current_user),
) -> FileContentResponse:
    _ensure_session(session_id, user)
    try:
        payload = file_service.read_file(session_id=session_id, owner_id=user.id, path=path)
    except FileAccessError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileContentResponse(**payload)
