"""Adapter interfaces that bridge agent tools with host capabilities."""

from __future__ import annotations

from typing import Protocol, TypedDict, Optional, Dict


class FileWriteResult(TypedDict):
    path: str
    size: int
    modified_at: float
    created: bool


class FileReadResult(TypedDict):
    path: str
    size: int
    modified_at: float
    content: str


class SandboxFileAdapter(Protocol):
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
    ) -> FileWriteResult: ...

    async def read_file(
        self,
        *,
        session_id: str,
        owner_id: str,
        path: str,
    ) -> FileReadResult: ...


class SandboxCommandResult(TypedDict):
    command: str
    exit_code: int
    stdout: str
    stderr: str


class SandboxCommandAdapter(Protocol):
    async def run_command(
        self,
        *,
        session_id: str,
        owner_id: str,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 300,
    ) -> SandboxCommandResult: ...
