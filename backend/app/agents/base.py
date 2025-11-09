from abc import ABC, abstractmethod
from typing import Any, Dict

class Agent(ABC):
    """
    Abstract base class for all agents.
    """
    def __init__(self, agent_name: str, session_id: str):
        self.agent_name = agent_name
        self.session_id = session_id

    @abstractmethod
    async def run(self, *args, **kwargs) -> Any:
        """
        The main execution method for the agent.
        """
        pass

    async def report_to_mike(self, result: Any):
        """
        Sends the result of a completed task back to the Mike agent.
        This will be implemented with message routing later.
        """
        print(f"Agent {self.agent_name} reporting to Mike with result: {result}")
        # In a real implementation, this would use the MessageRouter.
        pass