from app.agents.base import Agent
from app.services.agent_manager import agent_manager
from typing import Any

class BobAgent(Agent):
    """
    The Architect agent for system design and technical architecture.
    """
    async def run(self, task_description: str) -> Any:
        print(f"BobAgent: Received task - '{task_description}'")
        result = "System architecture designed."
        await self.report_to_mike(result)
        return result

agent_manager.register_agent(BobAgent)