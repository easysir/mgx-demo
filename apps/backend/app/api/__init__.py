from fastapi import APIRouter

from app.api.v1 import auth, chat, sessions, stream, sandbox, files

api_router = APIRouter()
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(stream.router, tags=["stream"])
api_router.include_router(sandbox.router, prefix="/sandbox", tags=["sandbox"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
