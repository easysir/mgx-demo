from app.agents.base import Agent
from app.services.agent_manager import agent_manager
from typing import Any

class AlexAgent(Agent):
    """
    The Engineer agent responsible for coding and technical implementation.
    """
    async def run(self, task_description: str) -> Any:
        """
        Executes a development task.
        """
        print(f"AlexAgent: Received task - '{task_description}'")
        print("AlexAgent: Starting code implementation...")
        # Simulate coding work
        result = "Code for the feature has been implemented."
        print("AlexAgent: Task completed.")
        
        # Report back to Mike
        await self.report_to_mike(result)
        return result

# Register the agent with the manager
agent_manager.register_agent(AlexAgent)