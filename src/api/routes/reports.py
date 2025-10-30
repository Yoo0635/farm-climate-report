"""Report API: generate a detailed report from the Evidence Pack using LLM-1 only.

Logs prompt/output to files for traceability.
"""

from __future__ import annotations

import json
import logging
import time
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status

from src.services.aggregation.models import AggregateRequest
from src.services.reports.reporter import EvidenceReporter


logger = logging.getLogger(__name__)
router = APIRouter(tags=["reports"])
_reporter = EvidenceReporter()


@router.post("/api/report", status_code=status.HTTP_200_OK)
async def generate_report(payload: AggregateRequest, demo: bool | None = Query(None)) -> dict:
    effective_payload = payload if demo is None else payload.model_copy(update={"demo": demo})

    req_id = str(uuid4())
    started = time.perf_counter()
    try:
        result = await _reporter.generate(effective_payload)
    except ValueError as exc:
        _log_failure(effective_payload, req_id, started, demo, "bad_request", str(exc))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        _log_failure(effective_payload, req_id, started, demo, "internal_error", str(exc))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Report generation failed") from exc

    duration_ms = int((time.perf_counter() - started) * 1000)
    log_payload = {
        "req_id": req_id,
        "region": payload.region,
        "crop": payload.crop,
        "demo": demo if demo is not None else payload.demo,
        "duration_ms": duration_ms,
        "prompt_path": result.prompt_path,
        "output_path": result.output_path,
    }
    logger.info("report.completed %s", json.dumps(log_payload, ensure_ascii=False))

    return {
        "issued_at": result.issued_at,
        "detailed_report": result.detailed_report,
        "prompt_path": result.prompt_path,
        "output_path": result.output_path,
    }


def _log_failure(payload: AggregateRequest, req_id: str, started: float, demo: bool | None, reason: str, message: str) -> None:
    duration_ms = int((time.perf_counter() - started) * 1000)
    log_payload = {
        "req_id": req_id,
        "region": payload.region,
        "crop": payload.crop,
        "demo": demo if demo is not None else payload.demo,
        "reason": reason,
        "error": message,
        "duration_ms": duration_ms,
    }
    logger.warning("report.failed %s", json.dumps(log_payload, ensure_ascii=False))

