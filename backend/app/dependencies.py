import redis.asyncio as redis
from app.core.config import settings
from app.services.session_manager import SessionManager
from app.services.context_store import ContextStore

# Create a Redis connection pool
redis_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)

def get_redis_client() -> redis.Redis:
    """
    Provides a Redis client from the connection pool.
    """
    return redis.Redis(connection_pool=redis_pool)

def get_session_manager() -> SessionManager:
    """
    Dependency function to get a SessionManager instance.
    """
    return SessionManager(redis_client=get_redis_client())

def get_context_store() -> ContextStore:
    """
    Dependency function to get a ContextStore instance.
    """
    return ContextStore(redis_client=get_redis_client())