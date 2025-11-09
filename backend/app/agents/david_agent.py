from app.agents.base import Agent
from app.services.agent_manager import agent_manager
from typing import Any

class DavidAgent(Agent):
    """
    The Data Analyst agent for data analysis and visualization.
    """
    async def run(self, task_description: str) -> Any:
        print(f"DavidAgent: Received task - '{task_description}'")
        result = "Data analysis complete."
        await self.report_to_mike(result)
        return result

agent_manager.register_agent(DavidAgent)