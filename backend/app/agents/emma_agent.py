from app.agents.base import Agent
from app.services.agent_manager import agent_manager
from typing import Any

class EmmaAgent(Agent):
    """
    The Product Manager agent for requirement analysis and PRD writing.
    """
    async def run(self, task_description: str) -> Any:
        print(f"EmmaAgent: Received task - '{task_description}'")
        result = "Product requirements document created."
        await self.report_to_mike(result)
        return result

agent_manager.register_agent(EmmaAgent)