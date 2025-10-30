#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path

# 1) 프로젝트 포맷터 로드
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
try:
    from lib.format_ko import format_for_sms
except Exception:

    def format_for_sms(data):
        title = data.get("title") or data.get("summary") or "알림"
        todo = data.get("todo") or []
        steps = "\n".join([f"• {t.get('step','')}" for t in todo]) if todo else ""
        area, crop = data.get("area", ""), data.get("crop", "")
        deadline = data.get("deadline", "")
        head = f"[{area} {crop}] {title}".strip()
        return "\n".join(
            [head, data.get("summary", ""), steps, f"마감: {deadline}"]
        ).strip()


# 2) .env 로드 (루트/백엔드 둘 다 시도)
from dotenv import load_dotenv

root_env = Path(__file__).resolve().parents[1] / ".env"
back_env = Path(__file__).resolve().parents[1] / "parut-backend" / ".env"
for env_path in (root_env, back_env):
    if env_path.exists():
        load_dotenv(env_path, override=False)

LEGACY_ENV_NAMES = {
    "SOLAPI_ACCESS_KEY": ["SOLAPI_API_KEY"],
    "SOLAPI_SECRET_KEY": ["SOLAPI_API_SECRET"],
    "SOLAPI_SENDER_NUMBER": ["SOLAPI_FROM_NUMBER"],
}


def _env(name: str) -> tuple[str | None, bool]:
    current = os.getenv(name)
    if current:
        return current, False
    for legacy in LEGACY_ENV_NAMES.get(name, []):
        legacy_value = os.getenv(legacy)
        if legacy_value:
            return legacy_value, True
    return None, False


API_KEY, key_from_legacy = _env("SOLAPI_ACCESS_KEY")
API_SECRET, secret_from_legacy = _env("SOLAPI_SECRET_KEY")
FROM, sender_from_legacy = _env("SOLAPI_SENDER_NUMBER")

if key_from_legacy or secret_from_legacy or sender_from_legacy:
    print(
        "[WARN] Legacy SOLAPI_* variables detected; migrate to "
        "SOLAPI_ACCESS_KEY / SOLAPI_SECRET_KEY / SOLAPI_SENDER_NUMBER.",
        file=sys.stderr,
    )

# 3) Solapi 준비(키 없으면 드라이런)
DRY_SEND = False
if not (API_KEY and API_SECRET and FROM):
    print(
        "[WARN] SOLAPI 키/시크릿/발신번호가 없어 드라이런 모드로 전환합니다.",
        file=sys.stderr,
    )
    DRY_SEND = True
else:
    from solapi.model import RequestMessage

    from solapi import SolapiMessageService

    svc = SolapiMessageService(api_key=API_KEY, api_secret=API_SECRET)


def send_sms(to: str, text: str):
    if DRY_SEND:
        return {
            "to": to,
            "group_id": None,
            "failed": [
                {"status_code": "DRYRUN", "status_message": "환경변수 없음(드라이런)"}
            ],
        }
    try:
        msg = RequestMessage(from_=FROM, to=to, text=text)
        resp = svc.send(msg)
        gid = getattr(getattr(resp, "group_info", None), "group_id", None)
        fm = getattr(resp, "failed_messages", None)
        failed = []
        if fm:
            for f in fm:
                failed.append(
                    {
                        "status_code": getattr(f, "status_code", None),
                        "status_message": getattr(f, "status_message", None),
                    }
                )
        return {"to": to, "group_id": gid, "failed": failed or None}
    except Exception as e:
        out = [{"exception": repr(e)}]
        fm = getattr(e, "failed_messages", None)
        if fm:
            out = []
            for f in fm:
                out.append(
                    {
                        "status_code": getattr(f, "status_code", None),
                        "status_message": getattr(f, "status_message", None),
                    }
                )
        return {"to": to, "group_id": None, "failed": out}


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def main():
    ap = argparse.ArgumentParser(description="Send SMS from dummy LLM results (JSONL)")
    ap.add_argument("--file", default="data/dummy_llm_results.jsonl", help="JSONL path")
    ap.add_argument("--to", help="Override recipients (comma-separated)")
    ap.add_argument("--max", type=int, default=0, help="Max records to send (0 = all)")
    ap.add_argument("--dry-run", action="store_true", help="Force dry-run")
    args = ap.parse_args()

    if args.dry_run:
        global DRY_SEND
        DRY_SEND = True

    src = Path(args.file)
    if not src.exists():
        print(f"[ERR] 파일 없음: {src}", file=sys.stderr)
        sys.exit(2)

    log_path = Path("out/sent_log.jsonl")
    sent = 0
    with log_path.open("a", encoding="utf-8") as logf:
        for i, rec in enumerate(iter_jsonl(src), start=1):
            if args.max and sent >= args.max:
                break
            body = format_for_sms(rec).strip()
            recipients = [
                x.strip()
                for x in (args.to.split(",") if args.to else rec.get("recipients", []))
                if x.strip()
            ]
            if not recipients:
                print(f"[SKIP] recipients 없음 @ line {i}", file=sys.stderr)
                continue
            for to in recipients:
                res = send_sms(to, body)
                logf.write(
                    json.dumps(
                        {"src_line": i, "from": FROM, "result": res}, ensure_ascii=False
                    )
                    + "\n"
                )
                print(json.dumps(res, ensure_ascii=False))
                sent += 1
    print(
        json.dumps(
            {"ok": True, "from": FROM, "sent": sent, "log": str(log_path)},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
