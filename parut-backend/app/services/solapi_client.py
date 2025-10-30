import datetime
import hashlib
import hmac
import os
import secrets
from typing import List, Optional, Tuple

import httpx
from dotenv import load_dotenv
from solapi.model import RequestMessage

from solapi import SolapiMessageService

load_dotenv(override=True)

_API_KEY = os.getenv("SOLAPI_API_KEY")
_API_SECRET = os.getenv("SOLAPI_API_SECRET")
_FROM = os.getenv("SOLAPI_FROM_NUMBER")
DRYRUN = os.getenv("DRYRUN", "1") == "1"

_svc: Optional[SolapiMessageService]
if DRYRUN:
    _svc = None
elif not (_API_KEY and _API_SECRET and _FROM):
    raise RuntimeError(
        "SOLAPI env vars missing: SOLAPI_API_KEY / SOLAPI_API_SECRET / SOLAPI_FROM_NUMBER"
    )
else:
    _svc = SolapiMessageService(api_key=_API_KEY, api_secret=_API_SECRET)


def _dryrun_detail(channel: str, quick_present: bool) -> dict:
    marker = {"status_code": "DRYRUN", "status_message": "dry-run mode"}
    detail = {"rcs_failed": None, "sms_failed": None}
    if quick_present:
        detail["rcs_failed"] = [marker]
    if not quick_present or channel == "SMS":
        detail["sms_failed"] = [marker]
    return {"channel": channel, "group_id": None, "detail": detail}


def _self_detail(channel: str, quick_present: bool) -> dict:
    marker = {"status_code": "SELF", "status_message": "sender equals recipient"}
    detail = {"rcs_failed": None, "sms_failed": [marker]}
    if quick_present:
        detail["rcs_failed"] = [marker]
    return {
        "channel": channel,
        "group_id": None,
        "detail": detail,
        "error": "SenderEqualsRecipient",
    }


def _byte_len(s: str) -> int:
    return len(s.encode("utf-8"))


def _auth_header() -> dict:
    date = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    salt = secrets.token_hex(8)
    sig = hmac.new(
        _API_SECRET.encode(), (date + salt).encode(), hashlib.sha256
    ).hexdigest()
    return {
        "Authorization": f"HMAC-SHA256 apiKey={_API_KEY}, date={date}, salt={salt}, signature={sig}"
    }


def _send_rest(messages: list[dict]):
    url = "https://api.solapi.com/messages/v4/send-many/detail"
    headers = {"Content-Type": "application/json", **_auth_header()}
    with httpx.Client(timeout=20) as client:
        r = client.post(url, headers=headers, json={"messages": messages})
        if r.status_code >= 400:
            raise Exception(f"REST {r.status_code}: {r.text}")
        data = r.json()
    failed = data.get("failedMessageList") or data.get("failed_message_list") or []
    gid = data.get("groupId") or data.get("group_id")
    return data, failed, gid


def _mk_sms_message(to: str, text: str) -> dict:
    return {"from": _FROM, "to": to, "text": text, "type": "SMS"}


def _mk_rcs_message(to: str, text: str, quick: List[Tuple[str, str]]) -> dict:
    typ = "RCS_LMS" if _byte_len(text) > 90 else "RCS_SMS"
    return {
        "from": _FROM,
        "to": to,
        "text": text,
        "type": typ,
        "rcsOptions": {
            "quickReplies": [
                {"label": lbl, "payload": payload} for lbl, payload in quick
            ],
            "disableSms": True,
        },
    }


def _normalize_failed(lst):
    out = []
    for f in lst:
        if isinstance(f, dict):
            out.append(
                {
                    "status_code": f.get("statusCode") or f.get("code"),
                    "status_message": f.get("statusMessage") or f.get("message"),
                }
            )
        else:
            out.append({"exception": repr(f)})
    return out or None


def _gid(resp) -> Optional[str]:
    return getattr(getattr(resp, "group_info", None), "group_id", None)


def _send_sms_via_sdk(to: str, text: str):
    if _svc is None:
        raise RuntimeError("Solapi SDK unavailable in dry-run mode")
    msg = RequestMessage(from_=_FROM, to=to, text=text)
    resp = _svc.send(msg)
    return {"channel": "SMS", "group_id": _gid(resp)}


def send_rcs_or_sms(
    to: str, text: str, quick=[("완료", "1"), ("도움요청", "2"), ("보류", "3")]
):
    quick_present = bool(quick)
    if (_FROM or "") and to.strip() == (_FROM or "").strip():
        return _self_detail(
            "RCS" if quick_present else "SMS",
            quick_present,
        )
    if DRYRUN:
        return _dryrun_detail("RCS" if quick_present else "SMS", quick_present)
    detail = {"rcs_failed": None, "sms_failed": None}
    if not quick:
        try:
            r = _send_sms_via_sdk(to, text)
            return {**r, "detail": detail}
        except Exception as ee:
            detail["sms_failed"] = [{"exception": repr(ee)}]
            return {
                "channel": "SMS",
                "group_id": None,
                "detail": detail,
                "error": "MessageNotReceived",
            }
    try:
        data, failed, gid = _send_rest([_mk_rcs_message(to, text, quick)])
        if failed:
            detail["rcs_failed"] = _normalize_failed(failed)
            try:
                r = _send_sms_via_sdk(to, text)
                return {**r, "detail": detail}
            except Exception as ee:
                detail["sms_failed"] = [{"exception": repr(ee)}]
                return {
                    "channel": "SMS",
                    "group_id": None,
                    "detail": detail,
                    "error": "MessageNotReceived",
                }
        return {"channel": "RCS", "group_id": gid, "detail": detail}
    except Exception as e:
        detail["rcs_failed"] = [{"exception": repr(e)}]
        try:
            r = _send_sms_via_sdk(to, text)
            return {**r, "detail": detail}
        except Exception as ee:
            detail["sms_failed"] = [{"exception": repr(ee)}]
            return {
                "channel": "SMS",
                "group_id": None,
                "detail": detail,
                "error": "MessageNotReceived",
            }


def send_sms(to: str, text: str):
    return send_rcs_or_sms(to, text, quick=[])
