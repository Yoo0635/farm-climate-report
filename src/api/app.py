"""FastAPI application entrypoint for the MVP."""

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Load environment variables before importing modules that may use them
load_dotenv(dotenv_path=Path(".env"))

from src.api.routes import aggregate, briefs, public, webhook


def create_app() -> FastAPI:
    """Application factory to ease testing."""
    app = FastAPI(title="Farm Climate Reporter MVP")

    @app.get("/health", tags=["health"])
    def healthcheck() -> dict[str, str]:
        """Lightweight health endpoint for deployment checks."""
        return {"status": "ok"}

    app.include_router(briefs.router)
    app.include_router(public.router)
    app.include_router(webhook.router)
    app.include_router(aggregate.router)
    app.mount("/static", StaticFiles(directory="src/templates/static"), name="static")

    return app


app = create_app()
