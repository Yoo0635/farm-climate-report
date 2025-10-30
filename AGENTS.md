# Repository Guidelines

## Project Structure & Module Organization
- `src/api/` FastAPI app and routers (entry: `src/api/app.py`, `app = create_app()`).
- `src/services/` Domain services (aggregation, briefs, llm, sms, store, etc.).
- `src/lib/` Shared models, formatting, and policy helpers.
- `src/db/` SQLAlchemy session/models; Alembic config in project root.
- `src/templates/` Jinja2 templates and static assets.
- `tests/` Pytest suite (`tests/test_*.py`).
- `frontend/` Vite + React + TypeScript console.
- `scripts/` Utilities like `scripts/demo_smoke.sh`, `scripts/pipeline_preview.py`.
- `specs/` API contracts and plans; `docs/` supplementary guides.

## Build, Test, and Development Commands
- Backend (local): `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
- Run API (reload): `uvicorn src.api.app:app --reload`
- Tests: `pytest -q` (set `LLM_OFFLINE=1` to avoid network/keys)
- DB migrations: `alembic upgrade head` (create: `alembic revision -m "msg" --autogenerate`)
- Frontend: `cd frontend && npm i && npm run dev` (build: `npm run build`)
- Docker Compose: `docker compose up --build` (publishes API on `:8080`)
- Smoke demo: `API_BASE=http://127.0.0.1:8000 ./scripts/demo_smoke.sh`

## Testing Guidelines
- Use Pytest; name files `tests/test_*.py`, functions `test_*`.
- API tests: `fastapi.testclient.TestClient`; async logic via `asyncio.run(...)`.

## Commit & Pull Request Guidelines
- Commit style: Conventional Commits (e.g., `feat(api): add aggregation endpoint`, `fix: handle None payload`).
- PRs must include: scope/intent, notes on testing (`pytest` output), screenshots for UI, and sample requests/responses for API changes.
- Update `specs/*` and `docs/*` when changing contracts; run Alembic for DB impacts and include migration notes.
