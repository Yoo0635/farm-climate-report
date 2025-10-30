"""Inbound SMS webhook handling."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.services.keywords.handler import KeywordHandler
from src.services.sms.solapi_client import SolapiClient, SolapiError

router = APIRouter(prefix="/api/sms", tags=["sms"])

_handler: KeywordHandler | None = None
_sms_client: SolapiClient | None = None


def _get_handler() -> KeywordHandler:
    global _handler
    if _handler is None:
        _handler = KeywordHandler()
    return _handler


def _get_sms_client() -> SolapiClient:
    global _sms_client
    if _sms_client is None:
        _sms_client = SolapiClient()
    return _sms_client


class InboundMessage(BaseModel):
    sender: str = Field(..., alias="from")
    recipient: str = Field(..., alias="to")
    message: str
    timestamp: str | None = None


@router.post("/webhook", status_code=status.HTTP_200_OK)
def receive_sms(payload: InboundMessage) -> dict[str, str]:
    profile_id = payload.sender
    try:
        handler = _get_handler()
        response_text = handler.handle(profile_id, payload.message)
        sms_client = _get_sms_client()
        sms_client.send_sms(profile_id, response_text)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
    except SolapiError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc

    return {"status": "ok"}
