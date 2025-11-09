from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create FastAPI application instance."""
    app = FastAPI(title="MGX Backend", version="0.1.0")

    @app.get("/healthz", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

