from .executor import AgentExecutor, WorkflowContext
from ..config import default_registry
from ..workflows.orchestrator import SequentialWorkflow
from ..tools.registry import get_tool_executor

_ORCHESTRATOR: AgentExecutor | None = None


def get_agent_orchestrator() -> AgentExecutor:
    """Singleton accessor so the FastAPI gateway can share orchestrator state."""
    global _ORCHESTRATOR
    if _ORCHESTRATOR is None:
        _ORCHESTRATOR = AgentExecutor(
            registry=default_registry,
            workflow=SequentialWorkflow(),
            tool_executor=get_tool_executor(),
        )
    return _ORCHESTRATOR
__all__ = ['AgentExecutor', 'WorkflowContext', 'get_agent_orchestrator']
