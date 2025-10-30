"""FastAPI application entrypoint for the MVP."""

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def create_app() -> FastAPI:
    """Application factory to ease testing."""
    load_dotenv(dotenv_path=Path(".env"))

    from src.api.routes import aggregate, briefs, public, webhook

    app = FastAPI(title="Farm Climate Reporter MVP")

    @app.get("/health", tags=["health"])
    def healthcheck() -> dict[str, str]:
        """Lightweight health endpoint for deployment checks."""
        return {"status": "ok"}

    # API routes (must be registered before static file serving)
    app.include_router(briefs.router)
    app.include_router(public.router)
    app.include_router(webhook.router)
    app.include_router(aggregate.router)

    # Legacy static files
    app.mount("/static", StaticFiles(directory="src/templates/static"), name="static")

    # Serve React frontend if build exists (SPA mode with fallback)
    frontend_build_path = Path("frontend/dist")
    if frontend_build_path.exists():
        # Mount React static assets (JS, CSS, images, etc.)
        app.mount(
            "/assets",
            StaticFiles(directory=str(frontend_build_path / "assets")),
            name="assets",
        )

        # Serve React app at root with SPA fallback
        # This catches all remaining routes and serves index.html
        app.mount(
            "/",
            StaticFiles(directory=str(frontend_build_path), html=True),
            name="react-app",
        )

    return app


app = create_app()
