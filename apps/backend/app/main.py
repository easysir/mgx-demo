import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.services import sandbox_idle_reaper

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
)


def create_app() -> FastAPI:
    """Create FastAPI application instance."""
    app = FastAPI(title="MGX Backend", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")

    @app.on_event("startup")
    async def startup() -> None:
        await sandbox_idle_reaper.start()

    @app.on_event("shutdown")
    async def shutdown() -> None:
        await sandbox_idle_reaper.stop()

    @app.get("/healthz", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
