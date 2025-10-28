"""FastAPI application entrypoint for the MVP."""

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Load environment variables before importing modules that may use them
load_dotenv(dotenv_path=Path(".env"))

from src.api.routes import briefs, public, webhook


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
    app.mount("/static", StaticFiles(directory="src/templates/static"), name="static")

    # React 콘솔(정적) 서빙: 빌드 산출물이 존재할 경우에만 마운트
    try:
        frontend_dist = Path("frontend/dist")
        public_console = Path("public/console")
        if frontend_dist.exists():
            app.mount("/console", StaticFiles(directory=str(frontend_dist), html=True), name="console")
        elif public_console.exists():
            app.mount("/console", StaticFiles(directory=str(public_console), html=True), name="console")
    except Exception:
        # 정적 폴더 미존재 등은 무시(MVP)
        pass

    return app


app = create_app()
