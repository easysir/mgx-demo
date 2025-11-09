from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.endpoints import session as session_router
from app.api.v1.endpoints import chat as chat_router
from app.api.v1.endpoints import websocket as websocket_router
from app.api.v1.endpoints import sandbox as sandbox_router

# Import agent modules to ensure they are registered
import app.agents.mike_agent
import app.agents.alex_agent
import app.agents.emma_agent
import app.agents.bob_agent
import app.agents.david_agent
import app.agents.iris_agent

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Include the API routers
app.include_router(session_router.router, prefix=settings.API_V1_STR, tags=["sessions"])
app.include_router(chat_router.router, prefix=settings.API_V1_STR, tags=["chat"])
app.include_router(websocket_router.router, prefix=settings.API_V1_STR, tags=["websocket"])
app.include_router(sandbox_router.router, prefix=settings.API_V1_STR, tags=["sandbox"])


@app.on_event("shutdown")
async def shutdown_event():
    # Properly close the Redis connection pool
    from app.dependencies import redis_pool
    await redis_pool.disconnect()
    
    # Cleanup all sandboxes and preview servers
    from app.services.code_sandbox import sandbox_manager
    from app.services.preview_server import preview_manager
    await sandbox_manager.cleanup_all()
    await preview_manager.stop_all()

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME
    }