"""Aggregation API endpoint for consolidated climate evidence packs."""

from __future__ import annotations

import json
import logging
import time
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status

from src.services.aggregation import (
    AggregateEvidencePack,
    AggregateRequest,
    get_aggregation_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["aggregation"])
_service = get_aggregation_service()


@router.post(
    "/api/aggregate",
    response_model=AggregateEvidencePack,
    status_code=status.HTTP_200_OK,
)
async def aggregate_endpoint(
    payload: AggregateRequest, demo: bool | None = Query(None)
) -> AggregateEvidencePack:
    """
    Resolve a profile, fetch upstream sources, and consolidate into an evidence pack.

    Query parameter `demo=true` forces scripted demo data regardless of cached/live fetches.
    """

    effective_payload = (
        payload if demo is None else payload.model_copy(update={"demo": demo})
    )

    req_id = str(uuid4())
    started = time.perf_counter()

    try:
        result = await _service.aggregate(effective_payload)
    except ValueError as exc:
        _log_failure(effective_payload, req_id, started, demo, "bad_request", str(exc))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except NotImplementedError as exc:
        _log_failure(
            effective_payload, req_id, started, demo, "not_implemented", str(exc)
        )
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc)
        ) from exc
    except RuntimeError as exc:
        _log_failure(
            effective_payload, req_id, started, demo, "upstream_unavailable", str(exc)
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except Exception as exc:  # noqa: BLE001 - bubble unexpected failures
        _log_failure(
            effective_payload, req_id, started, demo, "internal_error", str(exc)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Aggregation failed",
        ) from exc

    fetched = {
        "kma": any("KMA" in src for src in result.climate.provenance),
        "om": any("Open-Meteo" in src for src in result.climate.provenance),
        "npms": bool(result.pest.provenance),
    }
    duration_ms = int((time.perf_counter() - started) * 1000)
    log_payload = {
        "req_id": req_id,
        "region": result.profile.region,
        "crop": result.profile.crop,
        "demo": demo if demo is not None else effective_payload.demo,
        "fetched": fetched,
        "cache_hit": False,
        "duration_ms": duration_ms,
    }
    logger.info("aggregate.completed %s", json.dumps(log_payload, ensure_ascii=False))

    return result


def _log_failure(
    payload: AggregateRequest,
    req_id: str,
    started: float,
    demo: bool | None,
    reason: str,
    message: str,
) -> None:
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
    logger.warning("aggregate.failed %s", json.dumps(log_payload, ensure_ascii=False))
