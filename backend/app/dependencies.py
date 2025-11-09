import redis.asyncio as redis
from app.core.config import settings
from app.services.session_manager import SessionManager
from app.services.context_store import ContextStore
from app.services.agent_manager import AgentManager, agent_manager
from app.services.llm_service import LLMService
from app.tools.tool_executor import ToolExecutor
from app.tools.filesystem_tool import FileSystemTool

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

def get_agent_manager() -> AgentManager:
    """
    Dependency function to get the global AgentManager instance.
    """
    return agent_manager

def get_llm_service() -> LLMService:
    """
    Dependency function to get a LLMService instance.
    """
    return LLMService()

def get_tool_executor() -> ToolExecutor:
    """
    Dependency function to get a ToolExecutor instance with registered tools.
    """
    executor = ToolExecutor()
    
    # 注册文件系统工具
    filesystem_tool = FileSystemTool()
    executor.register_tool(filesystem_tool)
    
    # 可以在这里注册更多工具
    # executor.register_tool(TerminalTool())
    # executor.register_tool(SearchTool())
    
    return executor