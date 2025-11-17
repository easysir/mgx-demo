from .agent_runtime import AgentRuntimeGateway, agent_runtime_gateway
from .auth import auth_service, AuthService
from .session_repository import (
    session_repository,
    SessionRepository,
    InMemorySessionRepository,
    FileSessionRepository,
)
from .container import (
    ALLOWED_PREVIEW_PORTS,
    ContainerManager,
    FileAccessError,
    FileService,
    FileServiceConfig,
    SandboxCommandResult,
    SandboxCommandService,
    SandboxConfig,
    SandboxError,
    SandboxIdleReaper,
    SandboxInstance,
    container_manager,
    file_service,
    sandbox_command_service,
    sandbox_idle_reaper,
)
from agents.container.watchers import file_watcher_manager, SandboxFileWatcherManager
from .stream import stream_manager

__all__ = [
    "AgentRuntimeGateway",
    "agent_runtime_gateway",
    "auth_service",
    "AuthService",
    "session_repository",
    "SessionRepository",
    "InMemorySessionRepository",
    "FileSessionRepository",
    "container_manager",
    "ContainerManager",
    "SandboxConfig",
    "SandboxInstance",
    "ALLOWED_PREVIEW_PORTS",
    "SandboxError",
    "file_service",
    "FileService",
    "FileServiceConfig",
    "FileAccessError",
    "SandboxCommandResult",
    "SandboxCommandService",
    "SandboxIdleReaper",
    "SandboxFileWatcherManager",
    "file_watcher_manager",
    "sandbox_file_capability",
    "sandbox_command_service",
    "sandbox_idle_reaper",
]


file_watcher_manager.set_broadcast_fn(
    lambda session_id, payload: stream_manager.broadcast(session_id, payload)
)
