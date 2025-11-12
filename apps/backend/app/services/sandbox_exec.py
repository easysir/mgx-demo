from __future__ import annotations

import asyncio
import shlex
import subprocess
from dataclasses import dataclass
from typing import Dict, Optional

from .container import container_manager, SandboxError


@dataclass(slots=True)
class SandboxCommandResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str


class SandboxCommandService:
    """Execute shell commands inside an existing sandbox container."""

    def __init__(self, *, default_shell: str = "/bin/bash") -> None:
        self._shell = default_shell

    async def run_command(
        self,
        *,
        session_id: str,
        owner_id: str,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 300,
    ) -> SandboxCommandResult:
        if not command or not command.strip():
            raise SandboxError("Command must not be empty")
        if timeout <= 0:
            raise SandboxError("Timeout must be positive")
        instance = container_manager.ensure_session_container(session_id=session_id, owner_id=owner_id)
        container_manager.mark_active(session_id)
        return await asyncio.to_thread(
            self._run_sync,
            instance.container_name,
            session_id,
            command.strip(),
            cwd,
            env or {},
            timeout,
        )

    def _run_sync(
        self,
        container_name: str,
        session_id: str,
        command: str,
        cwd: Optional[str],
        env: Dict[str, str],
        timeout: int,
    ) -> SandboxCommandResult:
        workdir = cwd.strip() if cwd else ""
        if workdir and workdir.startswith("/"):
            resolved = workdir
        elif workdir:
            resolved = f"/workspace/{workdir.lstrip('/')}"
        else:
            resolved = "/workspace"
        prefix = f"cd {shlex.quote(resolved)} && "
        final_command = prefix + command

        exec_cmd: list[str] = ["docker", "exec", "-i"]
        for key, value in env.items():
            exec_cmd += ["-e", f"{key}={value}"]
        exec_cmd += [container_name, self._shell, "-lc", final_command]

        result = subprocess.run(
            exec_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        container_manager.mark_active(session_id)
        return SandboxCommandResult(
            command=command,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )


sandbox_command_service = SandboxCommandService()

__all__ = ["SandboxCommandResult", "SandboxCommandService", "sandbox_command_service"]
