#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from solapi.model import RequestMessage

from solapi import SolapiMessageService

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
DRYRUN_ENABLED = os.getenv("DRYRUN", "1") == "1"
if not DRYRUN_ENABLED and not (API_KEY and API_SECRET and FROM):
    print(
        "[ERR] SOLAPI_* 값이 없습니다. (.env에 키/시크릿/발신번호 필요)",
        file=sys.stderr,
    )
    sys.exit(2)

svc = None
if not DRYRUN_ENABLED:
    svc = SolapiMessageService(api_key=API_KEY, api_secret=API_SECRET)


def send_sms(to: str, text: str):
    if DRYRUN_ENABLED:
        return {
            "to": to,
            "group_id": None,
            "failed": [
                {"status_code": "DRYRUN", "status_message": "dry-run mode enabled"}
            ],
        }
    if to == FROM:
        return {
            "to": to,
            "group_id": None,
            "failed": [{"status_code": "SELF", "status_message": "FROM과 TO가 동일"}],
        }
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


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--text")
    g.add_argument("--brief-json")
    p.add_argument("--to", required=True)
    args = p.parse_args()

    if args.text:
        body = args.text.strip()
    else:
        data = json.loads(Path(args.brief_json).read_text(encoding="utf-8"))
        body = format_for_sms(data).strip()

    results = []
    for to in [x.strip() for x in args.to.split(",") if x.strip()]:
        results.append(send_sms(to, body))

    print(
        json.dumps({"ok": True, "from": FROM, "results": results}, ensure_ascii=False)
    )
    if any(r.get("failed") for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
