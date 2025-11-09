from typing import Any, Dict, Optional

import redis.asyncio as redis

class ContextStore:
    """
    Stores and retrieves contextual information for each session using Redis.
    This includes conversation history, task plans, etc.
    """
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.prefix = "context"

    async def set_context(self, session_id: str, context_data: Dict[str, Any]):
        """
        Saves the entire context for a session.
        """
        await self.redis.set(f"{self.prefix}:{session_id}", str(context_data))

    async def get_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the entire context for a session.
        """
        context_str = await self.redis.get(f"{self.prefix}:{session_id}")
        if context_str:
            try:
                return eval(context_str)
            except (SyntaxError, NameError):
                return None
        return None

    async def update_context_key(self, session_id: str, key: str, value: Any):
        """
        Updates a specific key within the session's context.
        """
        current_context = await self.get_context(session_id) or {}
        current_context[key] = value
        await self.set_context(session_id, current_context)

    async def get_context_key(self, session_id: str, key: str) -> Optional[Any]:
        """
        Retrieves a specific key from the session's context.
        """
        current_context = await self.get_context(session_id)
        if current_context:
            return current_context.get(key)
        return None