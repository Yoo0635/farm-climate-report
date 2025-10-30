import json
from pathlib import Path
from typing import Any, Dict, Optional

from .llm_client import ask_llm

BASE = Path(__file__).resolve()
CANDIDATES = [
    BASE.parents[3] / "data" / "dummy_llm_results.jsonl",  # repo 루트/data
    BASE.parents[2] / "data" / "dummy_llm_results.jsonl",  # parut-backend/data
    Path.cwd() / "data" / "dummy_llm_results.jsonl",  # 현재 작업 디렉토리 기준
]


def _pick_dummy():
    for p in CANDIDATES:
        if p.exists():
            return p
    return CANDIDATES[0]


DUMMY_JSONL = _pick_dummy()
print(f"[workflows] using dummy file: {DUMMY_JSONL}")

SYSTEM = "너는 농업 컨설턴트다. 안전하고 간결하게, 농가 실무자가 바로 실행할 수 있게 한국어로 안내해라. 위험 작업은 주의 문구를 포함하고, 불확실하면 가정과 한계도 말해라."


def _load_latest_context_for(msisdn: str) -> Optional[Dict[str, Any]]:
    if not DUMMY_JSONL.exists():
        return None
    latest = None
    try:
        with open(DUMMY_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if msisdn and msisdn in (rec.get("recipients") or []):
                    latest = rec
    except Exception:
        return None
    return latest


def _compose_user_prompt(
    action: str, ctx: Optional[Dict[str, Any]], free_text: str | None = None
) -> str:
    base = {
        "area": ctx.get("area") if ctx else None,
        "crop": ctx.get("crop") if ctx else None,
        "stage": ctx.get("stage") if ctx else None,
        "title": ctx.get("title") if ctx else None,
        "summary": ctx.get("summary") if ctx else None,
        "todo": ctx.get("todo") if ctx else None,
        "deadline": ctx.get("deadline") if ctx else None,
        "free_text": free_text,
    }
    if action == "DONE":
        instruct = (
            "작업 완료 보고다. 완료 확인과 후속 관리 2~3가지만 핵심 bullet로 제시해라."
        )
    elif action == "HELP":
        instruct = "도움 요청이다. 가능한 원인 진단 체크리스트와 즉시 가능한 응급 조치 3개 이내로 bullet로 제시해라."
    elif action == "SKIP":
        instruct = "보류 요청이다. 오늘은 쉬고 내일 아침에 할 2~3개의 짧은 할 일과 간단한 근거를 bullet로 제시해라."
    else:
        instruct = "자유 입력이다. 사용자의 메시지를 농업 컨설팅 톤으로 간단히 답해라."
    return f"지시: {instruct}\n컨텍스트(JSON):\n{json.dumps(base, ensure_ascii=False)}"


def run_numeric_workflow(
    msisdn: str, code: str, free_text: str | None = None
) -> Dict[str, Any]:
    action = {"1": "DONE", "2": "HELP", "3": "SKIP"}.get(code, "FREE")
    ctx = _load_latest_context_for(msisdn)
    prompt = _compose_user_prompt(action, ctx, free_text)
    reply = ask_llm(SYSTEM, prompt)
    menu = "회신: 1 완료보고 / 2 도움요청 / 3 보류"
    body = f"{reply}\n\n{menu}"
    return {"action": action, "context_found": bool(ctx), "body": body}
