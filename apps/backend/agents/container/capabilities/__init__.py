"""Sandbox capabilities exposed as agent tool adapters."""

from __future__ import annotations

from typing import Any, Dict, Awaitable, Callable

from agents.tools import (
    SandboxFileAdapter,
    FileWriteResult,
    FileReadResult,
    SandboxCommandAdapter,
    SandboxCommandResult,
)

from ..services.container import container_manager
from ..services.filesystem import FileService, FileAccessError, file_service
from ..services.sandbox_exec import SandboxCommandService, sandbox_command_service
from ...stream import file_change_event

FileChangeHook = Callable[[str, Dict[str, Any]], Awaitable[None]]


class SandboxFileCapability(SandboxFileAdapter):
    """Bridges agent tools to the actual sandbox file service."""

    def __init__(self, service: FileService) -> None:
        self._files = service
        self._hook: FileChangeHook | None = None

    def set_file_change_hook(self, hook: FileChangeHook | None) -> None:
        self._hook = hook

    async def write_file(
        self,
        *,
        session_id: str,
        owner_id: str,
        path: str,
        content: str,
        overwrite: bool = True,
        append: bool = False,
        encoding: str = 'utf-8',
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
        finally:
            container_manager.mark_active(session_id)

        if self._hook:
            await self._hook(
                session_id,
                file_change_event([payload['path']]),
            )
        return {
            'path': payload['path'],
            'size': payload['size'],
            'modified_at': payload['modified_at'],
            'created': payload['created'],
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
        finally:
            container_manager.mark_active(session_id)
        return {
            'path': payload['path'],
            'size': payload['size'],
            'modified_at': payload['modified_at'],
            'content': payload['content'],
        }


sandbox_file_capability = SandboxFileCapability(file_service)


class SandboxCommandCapability(SandboxCommandAdapter):
    def __init__(self, service: SandboxCommandService) -> None:
        self._service = service

    async def run_command(
        self,
        *,
        session_id: str,
        owner_id: str,
        command: str,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout: int = 300,
    ) -> SandboxCommandResult:
        result = await self._service.run_command(
            session_id=session_id,
            owner_id=owner_id,
            command=command,
            cwd=cwd,
            env=env,
            timeout=timeout,
        )
        return {
            'command': result.command,
            'exit_code': result.exit_code,
            'stdout': result.stdout,
            'stderr': result.stderr,
        }


sandbox_command_capability = SandboxCommandCapability(sandbox_command_service)

__all__ = [
    'sandbox_file_capability',
    'SandboxFileCapability',
    'sandbox_command_capability',
    'SandboxCommandCapability',
    'FileChangeHook',
]
