import uuid
from typing import Optional, Dict, Any

import redis.asyncio as redis
from pydantic import BaseModel

class Session(BaseModel):
    session_id: str
    user_id: str
    project_id: Optional[str] = None
    status: str = "active"
    working_directory: str
    context_data: Dict[str, Any] = {}

class SessionManager:
    """
    Manages user sessions using Redis.
    """
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def create_session(self, user_id: str, project_id: Optional[str] = None) -> Session:
        """
        Creates a new session for a user.
        """
        session_id = str(uuid.uuid4())
        working_directory = f"/workspace/user_sessions/{session_id}"
        
        session = Session(
            session_id=session_id,
            user_id=user_id,
            project_id=project_id,
            working_directory=working_directory
        )
        
        await self.redis.set(f"session:{session_id}", session.model_dump_json())
        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Retrieves a session by its ID.
        """
        session_data = await self.redis.get(f"session:{session_id}")
        if session_data:
            return Session.model_validate_json(session_data)
        return None

    async def update_session(self, session: Session) -> None:
        """
        Updates an existing session in Redis.
        """
        await self.redis.set(f"session:{session.session_id}", session.model_dump_json())

    async def delete_session(self, session_id: str) -> None:
        """
        Deletes a session from Redis.
        """
        await self.redis.delete(f"session:{session_id}")