"""Routes for triggering the personalized SMS brief."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.lib.models import Brief, DraftReport, Profile, RefinedReport
from src.lib.policy import validate_actions
from src.services.briefs.citations import append_citations
from src.services.briefs.generator import (
    BriefGenerationContext,
    BriefGenerationResult,
    BriefGenerator,
)
from src.services.briefs.sms_builder import build_sms
from src.services.links.link_service import LinkService
from src.services.signals.mappings import default_signals_actions
from src.services.sms.solapi_client import SolapiClient, SolapiError
from src.services.store.memory_store import StoredBrief, get_store

router = APIRouter(prefix="/api/briefs", tags=["briefs"])
logger = logging.getLogger(__name__)

DEFAULT_REGION = "Andong-si"
DEFAULT_CROP = "apple"
DEFAULT_STAGE = "flowering"

_store = get_store()
_generator: BriefGenerator | None = None
_sms_client: SolapiClient | None = None
_link_service: LinkService | None = None


def _get_generator() -> BriefGenerator:
    global _generator
    if _generator is None:
        _generator = BriefGenerator()
    return _generator


def _get_sms_client() -> SolapiClient:
    global _sms_client
    if _sms_client is None:
        _sms_client = SolapiClient()
    return _sms_client


def _get_link_service() -> LinkService:
    global _link_service
    if _link_service is None:
        _link_service = LinkService(
            base_url=os.environ.get(
                "DETAIL_BASE_URL", "https://parut.com/public/briefs"
            )
        )
    return _link_service


class BriefRequest(BaseModel):
    phone: str = Field(..., description="E.164 formatted phone number")
    region: str | None = Field(
        None, description=f"Optional. Defaults to {DEFAULT_REGION}."
    )
    crop: str | None = Field(
        None, description=f"Optional. Defaults to {DEFAULT_CROP}."
    )
    stage: str | None = Field(
        None, description=f"Optional. Defaults to {DEFAULT_STAGE}."
    )


class BriefResponse(BaseModel):
    brief_id: str
    message_preview: str


@router.post("", response_model=BriefResponse, status_code=status.HTTP_200_OK)
def create_brief(payload: BriefRequest) -> BriefResponse:
    """Generate a brief and dispatch SMS."""
    region = (payload.region or DEFAULT_REGION).strip() or DEFAULT_REGION
    crop = (payload.crop or DEFAULT_CROP).strip() or DEFAULT_CROP
    stage = (payload.stage or DEFAULT_STAGE).strip() or DEFAULT_STAGE

    profile = Profile(
        id=payload.phone,
        phone=payload.phone,
        region=region,
        crop=crop,
        stage=stage,
        language="ko",
        opt_in=True,
    )

    if _store.is_opted_out(profile.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User opted out of SMS."
        )

    _store.save_profile(profile)

    signals, actions = default_signals_actions()
    validate_actions(actions)
    date_range = f"{datetime.utcnow():%Y-%m-%d} ~ {(datetime.utcnow() + timedelta(days=14)):%Y-%m-%d}"

    try:
        generator = _get_generator()
        generation_result: BriefGenerationResult = generator.generate(
            BriefGenerationContext(
                profile=profile, signals=signals, actions=actions, date_range=date_range
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
    except Exception as exc:  # noqa: BLE001 - propagate as HTTP
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    if generation_result.prompt_path:
        logger.info(
            "brief.llm_logs %s",
            json.dumps(
                {
                    "prompt_path": generation_result.prompt_path,
                    "llm1_output_path": generation_result.output_path,
                    "llm2_output_path": generation_result.llm2_output_path,
                },
                ensure_ascii=False,
            ),
        )

    brief_id = str(uuid4())
    draft = DraftReport(
        id=str(uuid4()),
        brief_id=brief_id,
        content=generation_result.detailed_report,
        created_at=datetime.utcnow(),
    )
    refined_text = append_citations(generation_result.refined_report, actions)
    refined = RefinedReport(
        id=str(uuid4()),
        draft_id=draft.id,
        content=refined_text,
        created_at=datetime.utcnow(),
    )

    link_service = _get_link_service()
    link_record = link_service.create_link(brief_id)

    brief = Brief(
        id=brief_id,
        profile_id=profile.id,
        horizon_days=14,
        actions=actions,
        triggers=[signal.code for signal in signals],
        link_id=link_record.link_id,
        date_range=date_range,
        created_at=datetime.utcnow(),
    )

    sms_body = build_sms(refined_text, link_record.url)

    stored = StoredBrief(
        profile=profile,
        brief=brief,
        draft_report=draft,
        refined_report=refined,
        sms_body=sms_body,
        signals=signals,
    )
    _store.save_brief(stored)

    if sms_body.count("http") > 1:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Multiple links detected in SMS body",
        )

    try:
        sms_client = _get_sms_client()
        sms_client.send_sms(profile.phone, sms_body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
    except SolapiError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc

    preview = sms_body.splitlines()[0][:100]
    return BriefResponse(brief_id=brief_id, message_preview=preview)


class PreviewRequest(BaseModel):
    """Request to run the LLM pipeline without sending SMS."""

    region: str | None = Field(
        None, description=f"Optional. Defaults to {DEFAULT_REGION}."
    )
    crop: str | None = Field(
        None, description=f"Optional. Defaults to {DEFAULT_CROP}."
    )
    stage: str | None = Field(
        None, description=f"Optional. Defaults to {DEFAULT_STAGE}."
    )
    date_range_override: str | None = None


class PreviewResponse(BaseModel):
    """Raw pipeline outputs for inspection/testing (without legacy RAG fields)."""

    detailed_report: str
    refined_report: str
    sms_body: str


@router.post("/preview", response_model=PreviewResponse, status_code=status.HTTP_200_OK)
def preview_brief(payload: PreviewRequest) -> PreviewResponse:
    """Run RAG → LLM-1 → LLM-2 and return outputs; do not send SMS."""
    # Build a throwaway profile for pipeline inputs (no SMS dispatch)
    region = (payload.region or DEFAULT_REGION).strip() or DEFAULT_REGION
    crop = (payload.crop or DEFAULT_CROP).strip() or DEFAULT_CROP
    stage = (payload.stage or DEFAULT_STAGE).strip() or DEFAULT_STAGE

    profile = Profile(
        id="preview",
        phone="",
        region=region,
        crop=crop,
        stage=stage,
        language="ko",
        opt_in=True,
    )

    signals, actions = default_signals_actions()
    validate_actions(actions)
    date_range = (
        payload.date_range_override
        or f"{datetime.utcnow():%Y-%m-%d} ~ {(datetime.utcnow() + timedelta(days=14)):%Y-%m-%d}"
    )

    try:
        generator = _get_generator()
        generation_result: BriefGenerationResult = generator.generate(
            BriefGenerationContext(
                profile=profile, signals=signals, actions=actions, date_range=date_range
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
    except Exception as exc:  # noqa: BLE001 - propagate as HTTP
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    if generation_result.prompt_path:
        logger.info(
            "brief.preview.llm_logs %s",
            json.dumps(
                {
                    "prompt_path": generation_result.prompt_path,
                    "llm1_output_path": generation_result.output_path,
                    "llm2_output_path": generation_result.llm2_output_path,
                },
                ensure_ascii=False,
            ),
        )

    refined_text = append_citations(generation_result.refined_report, actions)
    # A preview SMS body is useful for end-to-end grasp; use a dummy link
    base_url = os.environ.get(
        "DETAIL_BASE_URL", "https://parut.com/public/briefs"
    ).rstrip("/")
    sms_body = build_sms(refined_text, link_url=f"{base_url}/preview")

    return PreviewResponse(
        detailed_report=generation_result.detailed_report,
        refined_report=refined_text,
        sms_body=sms_body,
    )
