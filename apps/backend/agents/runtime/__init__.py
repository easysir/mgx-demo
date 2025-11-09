from .orchestrator import AgentDispatch, AgentOrchestrator, WorkflowContext
from ..config import default_registry
from ..llm import get_llm_service
from ..workflows.default import DefaultWorkflow

_ORCHESTRATOR: AgentOrchestrator | None = None


def get_agent_orchestrator() -> AgentOrchestrator:
    """Singleton accessor so the FastAPI gateway can share orchestrator state."""
    global _ORCHESTRATOR
    if _ORCHESTRATOR is None:
        _ORCHESTRATOR = AgentOrchestrator(
            registry=default_registry,
            workflow=DefaultWorkflow(llm_service=get_llm_service()),
        )
    return _ORCHESTRATOR


__all__ = ['AgentDispatch', 'AgentOrchestrator', 'WorkflowContext', 'get_agent_orchestrator']
