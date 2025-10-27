"""Offline tests for the modularized LLM pipeline.

These tests validate RAG → LLM-1 → LLM-2 behaviour using fake LLMs, and the
preview endpoint which avoids SMS sending.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from src.lib.models import Profile, Signal, Action
from src.services.briefs.generator import BriefGenerationContext, BriefGenerator


def _set_offline_env() -> None:
    os.environ["LLM_OFFLINE"] = "1"
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("GEMINI_API_KEY", None)


def test_generator_offline_runs() -> None:
    _set_offline_env()
    generator = BriefGenerator()
    profile = Profile(id="p1", phone="", region="KR/Seoul", crop="Strawberry", stage="Flowering", language="ko")
    signals = [Signal(type="climate", code="HEATWAVE", severity="경보")]
    actions = [
        Action(title="낮 시간 차광막 조정", timing_window="당일 11:00 이전", trigger="기온 33°C 이상 예보", icon=None, source_name="농촌진흥청", source_year=2024)
    ]
    ctx = BriefGenerationContext(
        profile=profile,
        signals=signals,
        actions=actions,
        date_range=f"{datetime.utcnow():%Y-%m-%d} ~ {(datetime.utcnow() + timedelta(days=14)):%Y-%m-%d}",
    )
    result = generator.generate(ctx)
    assert result.detailed_report, "Detailed report should not be empty"
    assert result.refined_report, "Refined report should not be empty"
    # Fake LLMs introduce recognizable markers
    assert "2주 행동 보고서" in result.detailed_report


def test_preview_endpoint_offline() -> None:
    # Import FastAPI test client lazily to allow running without FastAPI installed
    try:
        from fastapi.testclient import TestClient  # type: ignore
        from src.api.app import create_app
    except Exception:
        import pytest
        pytest.skip("fastapi not installed in this environment")

    _set_offline_env()
    app = create_app()
    client = TestClient(app)
    payload = {"region": "KR/Seoul", "crop": "Strawberry", "stage": "Flowering", "scenario": "HEATWAVE"}
    resp = client.post("/api/briefs/preview", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    # Legacy RAG fields removed; ensure they are not present
    assert "rag_passages" not in data
    assert "web_findings" not in data
    # New minimal contract
    assert isinstance(data.get("detailed_report"), str) and data["detailed_report"]
    assert isinstance(data.get("refined_report"), str) and data["refined_report"]
    assert isinstance(data.get("sms_body"), str) and data["sms_body"]
