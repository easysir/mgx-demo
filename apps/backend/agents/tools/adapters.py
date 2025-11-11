"""Adapter interfaces that bridge agent tools with host capabilities."""

from __future__ import annotations

from typing import Protocol, TypedDict, Optional


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
