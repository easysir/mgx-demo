from app.agents.base import Agent
from app.services.agent_manager import agent_manager
from typing import Any

class MikeAgent(Agent):
    """
    The Team Leader agent responsible for planning, delegating, and reviewing tasks.
    """
    async def run(self, user_requirement: str) -> Any:
        """
        Analyzes the user requirement, creates a plan, and starts delegation.
        """
        print(f"MikeAgent: Analyzing requirement - '{user_requirement}'")
        # In a real scenario, this would involve complex planning and delegation logic.
        # For now, we'll just simulate a simple workflow.
        
        # 1. Create a task plan (simulated)
        plan = self._create_plan(user_requirement)
        
        # 2. Delegate the first task (e.g., to Alex)
        await self._delegate_task(plan)
        
        return "Plan created and first task delegated."

    def _create_plan(self, requirement: str) -> dict:
        """Simulates creating a task plan."""
        print("MikeAgent: Creating a task plan.")
        # This would be a more complex object in a real implementation.
        return {
            "requirement": requirement,
            "tasks": [
                {"agent": "alex", "task": "Develop the initial feature."}
            ]
        }

    async def _delegate_task(self, plan: dict):
        """Simulates delegating a task to another agent."""
        if plan["tasks"]:
            first_task = plan["tasks"][0]
            agent_name = first_task["agent"]
            task_description = first_task["task"]
            
            print(f"MikeAgent: Delegating task '{task_description}' to {agent_name.capitalize()}Agent.")
            
            # Get agent instance from manager
            # In a real scenario, this would trigger the agent's run method via a task scheduler.
            # alex_agent = agent_manager.get_agent_instance(agent_name, self.session_id)
            # await alex_agent.run(task_description)
            
# Register the agent with the manager
agent_manager.register_agent(MikeAgent)