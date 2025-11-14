from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Dict, Optional

from dotenv import dotenv_values

ALLOWED_PREVIEW_PORTS: list[int] = [4173, 5173, 3000]
APP_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
APP_ENV_VALUES: Dict[str, Optional[str]] = dotenv_values(APP_ENV_PATH) if APP_ENV_PATH.exists() else {}


def _config_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """配置读取顺序: container/.env -> 环境变量 -> 默认值。"""
    if key in APP_ENV_VALUES and APP_ENV_VALUES[key] is not None:
        return APP_ENV_VALUES[key]
    env_value = os.getenv(key)
    if env_value is not None:
        return env_value
    return default


class SandboxError(RuntimeError):
    """Raised when sandbox/container operations fail."""


class PortAllocationError(SandboxError):
    """Raised when no host ports are available for binding."""


def _parse_port_list(raw: str | None, fallback: list[int]) -> list[int]:
    if not raw:
        return fallback
    ports: list[int] = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            ports.append(int(chunk))
        except ValueError:
            continue
    return ports or fallback


def _parse_extra_env(raw: str | None) -> Dict[str, str]:
    if not raw:
        return {}
    envs: Dict[str, str] = {}
    for pair in raw.split(","):
        if "=" not in pair:
            continue
        key, value = pair.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key:
            envs[key] = value
    return envs


@dataclass(slots=True)
class SandboxConfig:
    """Runtime configuration for sandbox containers."""

    image: str = _config_value("SANDBOX_IMAGE", "mgx-sandbox:latest")
    base_path: Path = Path(_config_value("SANDBOX_BASE_PATH", "/tmp/mgx/sandboxes"))
    cpu_limit: str = _config_value("SANDBOX_CPU", "1")
    memory_limit: str = _config_value("SANDBOX_MEMORY", "1g")
    disable_network: bool = (_config_value("SANDBOX_DISABLE_NETWORK", "0") or "0") == "1"
    start_command: str = _config_value("SANDBOX_COMMAND", "tail -f /dev/null")
    exposed_ports: list[int] = field(
        default_factory=lambda: _parse_port_list(
            _config_value("SANDBOX_EXPOSED_PORTS"), ALLOWED_PREVIEW_PORTS
        )
    )
    port_range_start: int = int(_config_value("SANDBOX_PORT_START", "41000"))
    port_range_end: int = int(_config_value("SANDBOX_PORT_END", "42000"))
    custom_network: str | None = _config_value("SANDBOX_NETWORK") or None
    extra_env: Dict[str, str] = field(
        default_factory=lambda: _parse_extra_env(_config_value("SANDBOX_EXTRA_ENV"))
    )
    idle_timeout_seconds: int = int(_config_value("SANDBOX_IDLE_TIMEOUT", "1200"))
    gc_interval_seconds: int = int(_config_value("SANDBOX_GC_INTERVAL", "300"))
    preview_host: str = (_config_value("SANDBOX_PREVIEW_HOST", "http://127.0.0.1") or "http://127.0.0.1").rstrip("/")


@dataclass(slots=True)
class SandboxInstance:
    session_id: str
    owner_id: str
    container_name: str
    container_id: str
    workspace_path: Path
    port_map: Dict[int, int] = field(default_factory=dict)
    last_used: float = field(default_factory=lambda: time.time())


class PortAllocator:
    """本机端口分配器，确保在指定范围内分配不冲突的端口。"""

    def __init__(self, start: int, end: int) -> None:
        if start >= end:
            raise ValueError("Sandbox port range is invalid")
        self._start = start
        self._end = end
        self._lock = Lock()
        self._in_use: set[int] = set()

    def acquire(self) -> int:
        with self._lock:
            for port in range(self._start, self._end + 1):
                if port not in self._in_use:
                    self._in_use.add(port)
                    return port
        raise PortAllocationError("No available host ports for sandbox binding")

    def release(self, port: Optional[int]) -> None:
        if port is None:
            return
        with self._lock:
            self._in_use.discard(port)

    def reserve(self, port: Optional[int]) -> None:
        if port is None:
            return
        if port < self._start or port > self._end:
            return
        with self._lock:
            self._in_use.add(port)


class ContainerManager:
    """Minimal container lifecycle manager for local Docker sandboxes."""

    def __init__(self, config: Optional[SandboxConfig] = None) -> None:
        self.config = config or SandboxConfig()
        self.config.exposed_ports = ALLOWED_PREVIEW_PORTS.copy()
        self.config.base_path.mkdir(parents=True, exist_ok=True)
        self._instances: Dict[str, SandboxInstance] = {}
        self._port_allocator = PortAllocator(self.config.port_range_start, self.config.port_range_end)
        self._metadata_path = self.config.base_path / "sandboxes_meta.json"
        self._metadata_lock = Lock()
        self._metadata: Dict[str, Dict[str, object]] = self._load_metadata()
        self._restore_instances()

    def ensure_session_container(self, *, session_id: str, owner_id: str) -> SandboxInstance:
        """Return existing sandbox or create a new one for the session."""
        if session_id in self._instances:
            instance = self._instances[session_id]
            self._touch_instance(instance)
            return instance

        workspace_path = self.config.base_path / session_id
        workspace_path.mkdir(parents=True, exist_ok=True)
        container_name = f"mgx-session-{session_id}"

        existing_id = self._find_existing_container(container_name)
        if existing_id:
            port_map = self._inspect_port_bindings(container_name)
            self._reserve_ports(port_map)
            instance = SandboxInstance(
                session_id=session_id,
                owner_id=owner_id,
                container_name=container_name,
                container_id=existing_id,
                workspace_path=workspace_path,
                port_map=port_map,
            )
            self._touch_instance(instance)
            self._instances[session_id] = instance
            self._persist_instance(instance)
            return instance

        attempts = 0
        last_error: SandboxError | None = None
        while attempts < 3:
            attempts += 1
            port_map = self._allocate_ports()
            try:
                container_id = self._start_container_with_ports(
                    container_name=container_name,
                    workspace_path=workspace_path,
                    port_map=port_map,
                )
                break
            except SandboxError as exc:
                last_error = exc
                self._release_ports(port_map)
                if "port is already allocated" not in str(exc).lower():
                    raise
                continue
        else:
            raise last_error or SandboxError("Failed to start sandbox after retries")

        instance = SandboxInstance(
            session_id=session_id,
            owner_id=owner_id,
            container_name=container_name,
            container_id=container_id,
            workspace_path=workspace_path,
            port_map=port_map,
        )
        self._touch_instance(instance)
        self._instances[session_id] = instance
        self._persist_instance(instance)
        return instance

    def get_instance(self, session_id: str) -> SandboxInstance | None:
        instance = self._instances.get(session_id)
        if instance:
            self._touch_instance(instance)
        return instance

    def destroy_session_container(self, session_id: str) -> bool:
        """Stop and remove the sandbox container for the session."""
        instance = self._instances.pop(session_id, None)
        if not instance:
            return False
        try:
            self._stop_container(instance.container_name)
        finally:
            self._release_ports(instance.port_map)
            self._remove_metadata(session_id)
        return True

    def destroy_all(self, owner_id: Optional[str] = None) -> list[str]:
        """Destroy all sandboxes, optionally filtered by owner."""
        stopped: list[str] = []
        for session_id, instance in list(self._instances.items()):
            if owner_id and instance.owner_id != owner_id:
                continue
            try:
                self._stop_container(instance.container_name)
                self._release_ports(instance.port_map)
            finally:
                self._instances.pop(session_id, None)
                self._remove_metadata(session_id)
            stopped.append(session_id)
        return stopped

    def _start_container_with_ports(self, *, container_name: str, workspace_path: Path, port_map: Dict[int, int]) -> str:
        """Run docker container with a predefined port map and return container id."""
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
        elif self.config.custom_network:
            self._ensure_network(self.config.custom_network)
            cmd += ["--network", self.config.custom_network]
        for container_port, host_port in port_map.items():
            cmd += ["-p", f"{host_port}:{container_port}"]
        for key, value in (self.config.extra_env or {}).items():
            cmd += ["-e", f"{key}={value}"]
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

    def _allocate_ports(self) -> Dict[int, int]:
        if not self.config.exposed_ports:
            return {}
        port_map: Dict[int, int] = {}
        try:
            for container_port in self.config.exposed_ports:
                host_port = self._port_allocator.acquire()
                port_map[container_port] = host_port
        except PortAllocationError as exc:
            self._release_ports(port_map)
            raise SandboxError(str(exc)) from exc
        return port_map

    def _release_ports(self, port_map: Dict[int, int] | None) -> None:
        if not port_map:
            return
        for host_port in port_map.values():
            self._port_allocator.release(host_port)

    def _reserve_ports(self, port_map: Dict[int, int]) -> None:
        if not port_map:
            return
        for host_port in port_map.values():
            self._port_allocator.reserve(host_port)

    def _inspect_port_bindings(self, container_name: str) -> Dict[int, int]:
        result = subprocess.run(
            ["docker", "inspect", container_name, "--format", "{{json .NetworkSettings.Ports}}"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return {}
        try:
            data = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            return {}
        port_map: Dict[int, int] = {}
        for key, value in data.items():
            try:
                container_port = int(str(key).split("/")[0])
            except (ValueError, AttributeError):
                continue
            if not value:
                continue
            host_port = value[0].get("HostPort")
            if not host_port:
                continue
            try:
                port_map[container_port] = int(host_port)
            except ValueError:
                continue
        return port_map

    def _ensure_network(self, network_name: str) -> None:
        """确保自定义 Docker 网络存在，不存在则创建。"""
        if not network_name:
            return
        result = subprocess.run(
            ["docker", "network", "ls", "--filter", f"name={network_name}", "--format", "{{.Name}}"],
            capture_output=True,
            text=True,
        )
        names = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if network_name in names:
            return
        create = subprocess.run(["docker", "network", "create", network_name], capture_output=True, text=True)
        if create.returncode != 0:
            raise SandboxError(create.stderr.strip() or create.stdout.strip() or f"Failed to create network {network_name}")

    def _touch_instance(self, instance: SandboxInstance) -> None:
        instance.last_used = time.time()

    def mark_active(self, session_id: str) -> None:
        instance = self._instances.get(session_id)
        if instance:
            self._touch_instance(instance)
            self._persist_instance(instance)

    def cleanup_idle(self, *, now: Optional[float] = None) -> list[str]:
        timeout = self.config.idle_timeout_seconds
        if timeout <= 0:
            return []
        now_ts = now or time.time()
        idle_sessions: list[str] = []
        for session_id, instance in list(self._instances.items()):
            if now_ts - instance.last_used >= timeout:
                idle_sessions.append(session_id)
        for session_id in idle_sessions:
            try:
                self.destroy_session_container(session_id)
            except SandboxError:
                continue
        return idle_sessions

    def _load_metadata(self) -> Dict[str, Dict[str, object]]:
        if not self._metadata_path.exists():
            return {}
        try:
            raw = json.loads(self._metadata_path.read_text())
            if isinstance(raw, dict):
                return raw
        except Exception:
            pass
        return {}

    def _save_metadata(self) -> None:
        with self._metadata_lock:
            tmp = self._metadata_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self._metadata, ensure_ascii=False, indent=2))
            tmp.replace(self._metadata_path)

    def _persist_instance(self, instance: SandboxInstance) -> None:
        entry = {
            "owner_id": instance.owner_id,
            "last_used": instance.last_used,
            "port_map": instance.port_map,
        }
        self._metadata[instance.session_id] = entry
        self._save_metadata()

    def _remove_metadata(self, session_id: str) -> None:
        if session_id in self._metadata:
            self._metadata.pop(session_id)
            self._save_metadata()

    def _restore_instances(self) -> None:
        restored = 0
        for session_id, data in list(self._metadata.items()):
            owner_id = str(data.get("owner_id") or "")
            if not owner_id:
                self._metadata.pop(session_id, None)
                continue
            container_name = f"mgx-session-{session_id}"
            container_id = self._find_existing_container(container_name)
            if not container_id:
                self._metadata.pop(session_id, None)
                continue
            workspace_path = self.config.base_path / session_id
            port_map = self._inspect_port_bindings(container_name)
            if not port_map and isinstance(data.get("port_map"), dict):
                port_map = {int(k): int(v) for k, v in data.get("port_map", {}).items()}
            instance = SandboxInstance(
                session_id=session_id,
                owner_id=owner_id,
                container_name=container_name,
                container_id=container_id,
                workspace_path=workspace_path,
                port_map=port_map,
                last_used=float(data.get("last_used") or time.time()),
            )
            self._instances[session_id] = instance
            self._reserve_ports(port_map)
            restored += 1
        if restored:
            self._save_metadata()


container_manager = ContainerManager()
