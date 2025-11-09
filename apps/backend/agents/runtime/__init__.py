from .executor import AgentDispatch, AgentExecutor, WorkflowContext
from ..config import default_registry
from ..llm import get_llm_service
from ..workflows.orchestrator import SequentialWorkflow

_ORCHESTRATOR: AgentExecutor | None = None


def get_agent_orchestrator() -> AgentExecutor:
    """Singleton accessor so the FastAPI gateway can share orchestrator state."""
    global _ORCHESTRATOR
    if _ORCHESTRATOR is None:
        _ORCHESTRATOR = AgentExecutor(
            registry=default_registry,
            workflow=SequentialWorkflow(llm_service=get_llm_service()),
        )
    return _ORCHESTRATOR


__all__ = ['AgentDispatch', 'AgentExecutor', 'WorkflowContext', 'get_agent_orchestrator']
