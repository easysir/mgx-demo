from app.agents.base import Agent
from app.services.agent_manager import agent_manager
from typing import Any

class IrisAgent(Agent):
    """
    The Researcher agent for information gathering and web searching.
    """
    async def run(self, task_description: str) -> Any:
        print(f"IrisAgent: Received task - '{task_description}'")
        result = "Research complete."
        await self.report_to_mike(result)
        return result

agent_manager.register_agent(IrisAgent)