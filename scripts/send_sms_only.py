import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import find_dotenv, load_dotenv

# .env 로딩(루트/하위 모두 탐색)
load_dotenv(find_dotenv(usecwd=True), override=False)
here = Path(__file__).resolve()
for cand in [
    here.parents[1] / ".env",  # repo_root/.env
    here.parents[1] / "parut-backend/.env",  # repo_root/parut-backend/.env
]:
    if cand.exists():
        load_dotenv(cand, override=False)

SOLAPI_API_KEY = os.getenv("SOLAPI_API_KEY")
SOLAPI_API_SECRET = os.getenv("SOLAPI_API_SECRET")
SOLAPI_FROM = os.getenv("SOLAPI_FROM_NUMBER")

from solapi.model import RequestMessage

# SDK
from solapi import SolapiMessageService

svc = None
if SOLAPI_API_KEY and SOLAPI_API_SECRET:
    svc = SolapiMessageService(api_key=SOLAPI_API_KEY, api_secret=SOLAPI_API_SECRET)


def render_text(rec: Dict[str, Any]) -> str:
    steps = "\n".join([f"• {t.get('step')}" for t in rec.get("todo") or []]) or "• 없음"
    return (
        f"[{rec.get('area')} {rec.get('crop')}] {rec.get('title')}\n"
        f"- 권고: {rec.get('summary')}\n"
        f"- 작업:\n{steps}\n"
        f"- 마감: {rec.get('deadline')}"
    )


def to_list(s: str) -> List[str]:
    out = []
    for x in (s or "").split(","):
        x = x.strip()
        if x.isdigit():
            out.append(x)
    return list(dict.fromkeys(out))


def send_one(to: str, text: str) -> Dict[str, Any]:
    if not svc or not SOLAPI_FROM:
        return {
            "to": to,
            "group_id": None,
            "failed": [
                {"status_code": "DRYRUN", "status_message": "환경변수 없음(드라이런)"}
            ],
        }
    if to == SOLAPI_FROM:
        return {
            "to": to,
            "group_id": None,
            "failed": [{"status_code": "SELF", "status_message": "FROM과 TO가 동일"}],
        }
    try:
        msg = RequestMessage(from_=SOLAPI_FROM, to=to, text=text)
        resp = svc.send(msg)
        gid = getattr(getattr(resp, "group_info", None), "group_id", None)
        fm = getattr(resp, "failed_messages", None) or []
        if fm:
            return {
                "to": to,
                "group_id": None,
                "failed": [
                    {
                        "status_code": getattr(f, "status_code", None),
                        "status_message": getattr(f, "status_message", None),
                    }
                    for f in fm
                ],
            }
        return {"to": to, "group_id": gid, "failed": None}
    except Exception as e:
        return {"to": to, "group_id": None, "failed": [{"exception": repr(e)}]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--file",
        default=str((here.parents[1] / "data" / "llm_results.jsonl").resolve()),
    )
    ap.add_argument("--to", default="")
    ap.add_argument("--max", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = Path(args.file)
    outdir = here.parents[1] / "out"
    outdir.mkdir(parents=True, exist_ok=True)
    logf = outdir / "sent_log.jsonl"

    count = 0
    with src.open("r", encoding="utf-8") as f, logf.open("a", encoding="utf-8") as lf:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            body = render_text(rec)

            recips = (
                to_list(args.to)
                if args.to
                else to_list(",".join(rec.get("recipients") or []))
            )
            if not recips:
                lf.write(
                    json.dumps(
                        {
                            "src_line": i,
                            "from": SOLAPI_FROM,
                            "result": {"error": "NO_RECIPIENT"},
                        }
                    )
                    + "\n"
                )
                continue

            for to in recips:
                if args.max and count >= args.max:
                    break
                if args.dry_run:
                    res = {
                        "to": to,
                        "group_id": None,
                        "failed": [
                            {
                                "status_code": "DRYRUN",
                                "status_message": "사용자 요청(드라이런)",
                            }
                        ],
                    }
                else:
                    res = send_one(to, body)
                lf.write(
                    json.dumps(
                        {"src_line": i, "from": SOLAPI_FROM, "result": res},
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                print(json.dumps(res, ensure_ascii=False))
                count += 1
            if args.max and count >= args.max:
                break

    print(
        json.dumps(
            {"ok": True, "from": SOLAPI_FROM, "sent": count, "log": str(logf)},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
