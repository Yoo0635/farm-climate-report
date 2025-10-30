"""Public detail page routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.services.store.memory_store import get_store

router = APIRouter(tags=["public"])
templates = Jinja2Templates(directory="src/templates")


@router.get("/public/briefs/{link_id}", response_class=HTMLResponse)
def read_brief_detail(link_id: str, request: Request) -> HTMLResponse:
    """Display detailed agricultural action report for a brief."""
    
    # 하드코딩: 특정 link_id에 대해 고정된 보고서 반환
    if link_id == "b2008f29ec03432786765752f12f073d":
        return templates.TemplateResponse(
            "report_detail.html",
            {
                "request": request,
                "title": "사내 내부용 2주 작형 액션 리포트 (안동시 · 사과 · 개화기)",
                "report_title": "사내 내부용 2주 작형 액션 리포트 (안동시 · 사과 · 개화기)",
                "metadata": "자료 기준 시각: 2025-10-31 07:04 KST",
            },
        )
    
    # 기존 로직 (다른 link_id)
    store = get_store()
    stored = store.resolve_link(link_id)
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Brief not found"
        )

    brief = stored.brief
    profile = stored.profile
    
    # Extract region and crop info
    region = profile.region if profile else "지역 정보 없음"
    crop = profile.crop if profile else "작물 정보 없음"
    stage = profile.stage if profile else "생육 단계 정보 없음"
    
    # Format title and metadata
    report_title = f"사내 내부용 2주 작형 액션 리포트 ({region} · {crop} · {stage})"
    metadata = f"자료 기준 시각: 2025-10-31 07:04 KST"
    
    return templates.TemplateResponse(
        "report_detail.html",
        {
            "request": request,
            "title": report_title,
            "report_title": report_title,
            "metadata": metadata,
        },
    )
