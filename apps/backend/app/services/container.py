from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


class SandboxError(RuntimeError):
    """Raised when sandbox/container operations fail."""


@dataclass(slots=True)
class SandboxConfig:
    """Runtime configuration for sandbox containers."""

    image: str = os.getenv("SANDBOX_IMAGE", "node:18-bookworm")
    base_path: Path = Path(os.getenv("SANDBOX_BASE_PATH", "/tmp/mgx/sandboxes"))
    cpu_limit: str = os.getenv("SANDBOX_CPU", "1")
    memory_limit: str = os.getenv("SANDBOX_MEMORY", "1g")
    disable_network: bool = os.getenv("SANDBOX_DISABLE_NETWORK", "0") == "1"
    start_command: str = os.getenv("SANDBOX_COMMAND", "tail -f /dev/null")


@dataclass(slots=True)
class SandboxInstance:
    session_id: str
    owner_id: str
    container_name: str
    container_id: str
    workspace_path: Path


class ContainerManager:
    """Minimal container lifecycle manager for local Docker sandboxes."""

    def __init__(self, config: Optional[SandboxConfig] = None) -> None:
        self.config = config or SandboxConfig()
        self.config.base_path.mkdir(parents=True, exist_ok=True)
        self._instances: Dict[str, SandboxInstance] = {}

    def ensure_session_container(self, *, session_id: str, owner_id: str) -> SandboxInstance:
        """Return existing sandbox or create a new one for the session."""
        if session_id in self._instances:
            return self._instances[session_id]

        workspace_path = self.config.base_path / session_id
        container_name = f"mgx-session-{session_id}"

        existing_id = self._find_existing_container(container_name)
        if existing_id:
            instance = SandboxInstance(
                session_id=session_id,
                owner_id=owner_id,
                container_name=container_name,
                container_id=existing_id,
                workspace_path=workspace_path,
            )
            self._instances[session_id] = instance
            return instance

        workspace_path.mkdir(parents=True, exist_ok=True)
        container_id = self._start_container(container_name=container_name, workspace_path=workspace_path)

        instance = SandboxInstance(
            session_id=session_id,
            owner_id=owner_id,
            container_name=container_name,
            container_id=container_id,
            workspace_path=workspace_path,
        )
        self._instances[session_id] = instance
        return instance

    def destroy_session_container(self, session_id: str) -> bool:
        """Stop and remove the sandbox container for the session."""
        instance = self._instances.pop(session_id, None)
        if not instance:
            return False
        self._stop_container(instance.container_name)
        return True

    def destroy_all(self, owner_id: Optional[str] = None) -> list[str]:
        """Destroy all sandboxes, optionally filtered by owner."""
        stopped: list[str] = []
        for session_id, instance in list(self._instances.items()):
            if owner_id and instance.owner_id != owner_id:
                continue
            try:
                self._stop_container(instance.container_name)
            finally:
                self._instances.pop(session_id, None)
            stopped.append(session_id)
        return stopped

    def _start_container(self, *, container_name: str, workspace_path: Path) -> str:
        """Run docker container and return container id."""
        cmd = [
            "docker",
            "run",
            "-d",
            "--rm",
            "--cpus",
            self.config.cpu_limit,
            "--memory",
            self.config.memory_limit,
            "-v",
            f"{workspace_path}:/workspace",
            "--workdir",
            "/workspace",
            "--name",
            container_name,
        ]
        if self.config.disable_network:
            cmd += ["--network", "none"]
        cmd += [self.config.image, "bash", "-lc", self.config.start_command]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise SandboxError(f"Failed to start sandbox: {result.stderr.strip() or result.stdout.strip()}")
        return result.stdout.strip()

    def _find_existing_container(self, container_name: str) -> Optional[str]:
        result = subprocess.run([
            "docker",
            "ps",
            "-a",
            "--filter",
            f"name={container_name}",
            "--format",
            "{{.ID}} {{.Status}}"
        ], capture_output=True, text=True)
        if result.returncode != 0:
            return None
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if not lines:
            return None
        first = lines[0].split()[0]
        texture = ' '.join(lines[0].split()[1:])
        if texture.startswith('Up'):
            return first
        subprocess.run(["docker", "start", container_name], capture_output=True, text=True)
        inspect = subprocess.run(["docker", "ps", "-q", "--filter", f"name={container_name}"], capture_output=True, text=True)
        return inspect.stdout.strip() or first

    def _stop_container(self, container_name: str) -> None:
        """Stop docker container gracefully."""
        result = subprocess.run(["docker", "stop", container_name], capture_output=True, text=True)
        if result.returncode != 0 and "No such container" not in result.stderr:
            raise SandboxError(result.stderr.strip() or result.stdout.strip() or "Failed to stop container")


container_manager = ContainerManager()
