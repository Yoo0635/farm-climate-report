"""Public detail page routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.services.briefs.plan_b import generate_plan_b
from src.services.store.memory_store import get_store


router = APIRouter(tags=["public"])
templates = Jinja2Templates(directory="src/templates")


@router.get("/public/briefs/{link_id}", response_class=HTMLResponse)
def read_brief_detail(link_id: str, request: Request) -> HTMLResponse:
    store = get_store()
    stored = store.resolve_link(link_id)
    if not stored:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brief not found")

    brief = stored.brief
    actions = brief.actions
    checklist = [f"{action.timing_window} · {action.trigger}" for action in actions]
    sources = [
        {
            "name": action.source_name,
            "year": action.source_year,
        }
        for action in actions
    ]

    plan_b = generate_plan_b(stored.signals)

    refined_lines = stored.refined_report.content.splitlines() if stored.refined_report.content else []

    return templates.TemplateResponse(
        "detail.html",
        {
            "request": request,
            "title": f"{brief.profile_id} 농장 브리프",
            "summary_title": "2주 농장 행동 브리프",
            "summary_line1": actions[0].title if actions else "",
            "summary_line2": refined_lines[0] if refined_lines else "",
            "summary_line3": brief.date_range,
            "checklist": checklist,
            "plan_b": plan_b,
            "sources": sources,
            "detailed_report": stored.draft_report.content,
        },
    )
