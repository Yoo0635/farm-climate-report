import os
from typing import List, Optional

from app.services.solapi_client import send_rcs_or_sms
from app.services.workflows import run_numeric_workflow
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

load_dotenv()


class TodoItem(BaseModel):
    step: str
    materials: List[str] = []
    etaMin: Optional[int] = None


class AlertSpec(BaseModel):
    area: str
    crop: str
    stage: str
    title: str
    summary: str
    todo: List[TodoItem] = []
    deadline: str
    quickReplies: List[str] = []
    evidence: List[str] = []
    fallback: Optional[str] = None
    to: List[str]


WEBHOOK_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "")

app = FastAPI(title="Parut Backend", version="0.2")


def render_text(spec: AlertSpec) -> str:
    steps = "\n".join([f"• {t.step}" for t in spec.todo]) if spec.todo else "• 없음"
    return (
        f"[{spec.area} {spec.crop}] {spec.title}\n"
        f"- 권고: {spec.summary}\n"
        f"- 작업:\n{steps}\n"
        f"- 마감: {spec.deadline}\n"
        f"회신: 1완료 / 2도움 / 3보류"
    )


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.post("/send/alert")
def send_alert(spec: AlertSpec):
    text = render_text(spec)
    results = []
    for to in spec.to:
        quick = (
            [("완료", "1"), ("도움요청", "2"), ("보류", "3")]
            if spec.quickReplies
            else []
        )
        results.append({"to": to, **send_rcs_or_sms(to, text, quick)})
    return {"ok": True, "results": results}


@app.post("/webhook/solapi/inbound")
async def inbound(req: Request, x_verify_token: str | None = Header(default=None)):
    if WEBHOOK_TOKEN and x_verify_token != WEBHOOK_TOKEN:
        raise HTTPException(401, "bad token")

    payload = await req.json()
    print("INBOUND>>", payload)

    sender = (payload.get("from") or "").strip()
    text = (payload.get("text") or "").strip()
    payload_btn = (payload.get("payload") or "").strip()

    # 숫자 회신(버튼 payload 또는 SMS 숫자)
    val = (payload_btn or text).strip()
    code = val[:1] if val else ""
    wf = run_numeric_workflow(
        sender, code, free_text=(text if code not in ("1", "2", "3") else None)
    )
    reply_text = wf["body"]
    print("REPLY>>", reply_text[:200].replace("\n", " / "))
    try:
        # RCS 가능시 버튼 붙여 재발송(불가하면 자동 SMS 폴백)
        send_rcs_or_sms(
            sender, reply_text, [("완료", "1"), ("도움요청", "2"), ("보류", "3")]
        )
    except Exception as e:
        print("REPLY_SEND_FAIL>>", e)
    return {
        "ok": True,
        "from": sender,
        "code": code,
        "action": wf["action"],
        "context_found": wf["context_found"],
    }


@app.post("/webhook/solapi/status")
async def status(req: Request, x_verify_token: str | None = Header(default=None)):
    if WEBHOOK_TOKEN and x_verify_token != WEBHOOK_TOKEN:
        raise HTTPException(401, "bad token")
    payload = await req.json()
    print("STATUS>>", payload)
    return {"ok": True}
