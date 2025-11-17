"""Agent runtime package.

Houses agent definitions, workflows, tool adapters, and orchestrator logic.
For Phase 1 the code runs in-process with the FastAPI gateway, but the
interfaces are designed so we can lift this package into a dedicated service
once RPC boundaries are ready.
"""

from .runtime import AgentExecutor, WorkflowContext, get_agent_orchestrator

__all__ = ['AgentExecutor', 'WorkflowContext', 'get_agent_orchestrator']
