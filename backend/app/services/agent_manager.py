from typing import Dict, Type
from app.agents.base import Agent

class AgentManager:
    """
    Manages the lifecycle and execution of agent instances.
    In this simplified version, it holds a registry of available agent classes.
    """
    def __init__(self):
        self._agents: Dict[str, Type[Agent]] = {}

    def register_agent(self, agent_class: Type[Agent]):
        """
        Registers an agent class in the manager.
        """
        agent_name = agent_class.__name__.replace("Agent", "").lower()
        self._agents[agent_name] = agent_class
        print(f"Agent '{agent_name}' registered.")

    def get_agent_instance(self, agent_name: str, session_id: str) -> Agent:
        """
        Creates an instance of a requested agent.
        """
        agent_name = agent_name.lower()
        agent_class = self._agents.get(agent_name)
        if not agent_class:
            raise ValueError(f"Agent '{agent_name}' not found.")
        
        return agent_class(agent_name=agent_name, session_id=session_id)

# A global instance of the agent manager to be used across the application.
agent_manager = AgentManager()

def get_agent_manager() -> AgentManager:
    """
    Dependency function to get the global AgentManager instance.
    """
    return agent_manager