from __future__ import annotations

from typing import Any, Dict

from agents.tools import SandboxFileAdapter, FileWriteResult, FileReadResult

from app.services.filesystem import FileService, FileAccessError, file_service
from app.services.stream import stream_manager


class SandboxFileCapability(SandboxFileAdapter):
    """Bridges agent tools to the actual sandbox file service."""

    def __init__(self, service: FileService) -> None:
        self._files = service

    async def write_file(
        self,
        *,
        session_id: str,
        owner_id: str,
        path: str,
        content: str,
        overwrite: bool = True,
        append: bool = False,
        encoding: str = "utf-8",
    ) -> FileWriteResult:
        try:
            payload = self._files.write_file(
                session_id=session_id,
                owner_id=owner_id,
                path=path,
                content=content,
                overwrite=overwrite,
                append=append,
                encoding=encoding,
            )
        except FileAccessError as exc:
            raise FileAccessError(str(exc)) from exc

        await stream_manager.broadcast(
            session_id,
            {
                "type": "file_change",
                "paths": [payload["path"]],
            },
        )
        return {
            "path": payload["path"],
            "size": payload["size"],
            "modified_at": payload["modified_at"],
            "created": payload["created"],
        }

    async def read_file(
        self,
        *,
        session_id: str,
        owner_id: str,
        path: str,
    ) -> FileReadResult:
        try:
            payload = self._files.read_file(session_id=session_id, owner_id=owner_id, path=path)
        except FileAccessError as exc:
            raise FileAccessError(str(exc)) from exc
        return {
            "path": payload["path"],
            "size": payload["size"],
            "modified_at": payload["modified_at"],
            "content": payload["content"],
        }


sandbox_file_capability = SandboxFileCapability(file_service)

__all__ = ['sandbox_file_capability', 'SandboxFileCapability']
