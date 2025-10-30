#!/usr/bin/env python3
"""Fetch and summarize NPMS (NCPMS) pest bulletins for Andong apple."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from dataclasses import dataclass
from datetime import date, datetime
from html import unescape
from typing import Any
from urllib.parse import unquote, urlencode
from urllib.request import urlopen

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python <3.9 fallback
    from backports.zoneinfo import ZoneInfo  # type: ignore[no-redef]

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None

KST = ZoneInfo("Asia/Seoul")


@dataclass(frozen=True)
class ProbeConfig:
    api_key: str
    crop_code: str
    base_url: str = "http://ncpms.rda.go.kr/npmsAPI/service"


def build_npms_request(config: ProbeConfig) -> tuple[str, dict[str, str]]:
    params: dict[str, str] = {
        "apiKey": config.api_key,
        "serviceCode": "SVC31",
        "proxyUrl": "http://example.com/callback",
        "div_id": "result",
        "cropList": config.crop_code,
    }
    return config.base_url, params


def fetch_npms(config: ProbeConfig) -> dict[str, Any]:
    url, params = build_npms_request(config)
    request_url = f"{url}?{urlencode(params)}"
    with urlopen(request_url, timeout=20) as response:  # noqa: S310 - trusted hostname
        charset = response.headers.get_content_charset() or "utf-8"
        content = response.read().decode(charset)
    return json.loads(content)


def decode_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {key: decode_payload(val) for key, val in payload.items()}
    if isinstance(payload, list):
        return [decode_payload(item) for item in payload]
    if isinstance(payload, str):
        return unescape(unquote(payload))
    return payload


def summarize_npms(payload: dict[str, Any], crop_code: str) -> list[dict[str, Any]]:
    service = payload.get("service") or {}
    models = service.get("pestModelByKncrList") or []
    if isinstance(models, dict):
        models = [models]

    bulletins: list[dict[str, Any]] = []
    seen_pests: set[str] = set()

    for raw in models:
        entry = {
            _clean_text(str(k)): _clean_text(unquote(str(v))) for k, v in raw.items()
        }
        if entry.get("kncrCode") != crop_code:
            continue

        pest_name = entry.get("dbyhsMdlNm")
        if not pest_name or pest_name in seen_pests:
            continue

        risk_index = _to_int(entry.get("validAlarmRiskIdex"), default=1)
        segments = _parse_segments(entry.get("pestConfigStr", ""))
        summary, color = _select_segment(segments, risk_index)
        risk = _risk_from_index(risk_index, color)
        since = _parse_datetime(entry.get("nowDrveDatetm"))

        bulletins.append(
            {
                "pest": pest_name,
                "risk": risk,
                "since": since or date.today().isoformat(),
                "summary": summary or f"{pest_name} 경보가 활성화되어 있습니다.",
                "raw_index": risk_index,
            }
        )
        seen_pests.add(pest_name)

    bulletins.sort(key=lambda item: item["raw_index"])
    return bulletins


def _clean_text(value: str) -> str:
    if value in ("", "-", "None"):
        return ""
    unescaped = unescape(value.replace("&nbsp", " ").replace("\xa0", " "))
    return " ".join(unescaped.split())


def _to_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_segments(raw: str) -> list[tuple[str, str, str]]:
    segments: list[tuple[str, str, str]] = []
    for segment in raw.split("|"):
        parts = segment.split("!+@+!")
        if len(parts) != 3:
            continue
        title = _clean_text(parts[0])
        body = _clean_text(parts[1])
        color = parts[2].strip().upper()
        if not title and not body:
            continue
        segments.append((title, body, color))
    return segments


def _select_segment(
    segments: list[tuple[str, str, str]], index: int
) -> tuple[str | None, str | None]:
    if not segments:
        return None, None
    clamped = max(1, min(index, len(segments)))
    title, body, color = segments[clamped - 1]
    text = " ".join(part for part in (title, body) if part).strip() or None
    return text, color or None


def _risk_from_index(index: int, color: str | None) -> str:
    if index <= 1:
        return "ALERT"
    if index == 2:
        return "HIGH"
    if index == 3:
        return "MODERATE"
    return "LOW"


def _parse_datetime(value: str | None) -> str | None:
    if not value:
        return None
    for fmt in ("%Y%m%d%H%M", "%Y%m%d%H"):
        try:
            dt = datetime.strptime(value, fmt).replace(tzinfo=KST)
            return dt.date().isoformat()
        except ValueError:
            continue
    return None


def _format_curl(url: str, params: dict[str, str]) -> str:
    lines = ["curl -G --compressed \\", f"  {shlex.quote(url)} \\"]
    items = list(params.items())
    for idx, (key, value) in enumerate(items):
        rendered = "${NPMS_API_KEY}" if key == "apiKey" else value
        flag = f"--data-urlencode {shlex.quote(f'{key}={rendered}')}"
        suffix = "" if idx == len(items) - 1 else " \\"
        lines.append(f"  {flag}{suffix}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Probe NPMS/NCPMS pest forecast API.")
    parser.add_argument(
        "--npms-key", help="NPMS API key (defaults to NPMS_API_KEY env)."
    )
    parser.add_argument(
        "--crop",
        default=os.environ.get("NPMS_DEFAULT_CROP", "FT010601"),
        help="Crop code (default: FT010601 — 안동 사과).",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print full decoded JSON (truncated to 5000 chars).",
    )
    parser.add_argument(
        "--show-curl", action="store_true", help="Print curl command before fetching."
    )
    args = parser.parse_args(argv)

    if load_dotenv is not None:
        load_dotenv()

    api_key = args.npms_key or os.environ.get("NPMS_API_KEY")
    if not api_key:
        print(
            "NPMS key is missing. Set NPMS_API_KEY or pass --npms-key.", file=sys.stderr
        )
        return 1

    config = ProbeConfig(
        api_key=api_key,
        crop_code=args.crop,
        base_url=os.environ.get(
            "NPMS_API_BASE_URL", "http://ncpms.rda.go.kr/npmsAPI/service"
        ),
    )
    url, params = build_npms_request(config)

    if args.show_curl:
        print("=== Curl (NPMS SVC31) ===")
        print(_format_curl(url, params))

    try:
        raw = fetch_npms(config)
    except Exception as exc:  # noqa: BLE001 - CLI aid
        print(f"Failed to fetch NPMS data: {exc}", file=sys.stderr)
        return 1

    decoded = decode_payload(raw)
    bulletins = summarize_npms(decoded, config.crop_code)

    issued_at = datetime.now(tz=KST).isoformat()
    print(f"=== NPMS Summary ({issued_at}) ===")
    if not bulletins:
        print("No bulletins available for the requested crop.")
    else:
        for idx, entry in enumerate(bulletins, start=1):
            print(f"{idx}. {entry['pest']} — {entry['risk']} (since {entry['since']})")
            print(f"   {entry['summary']}")

    if args.raw:
        text = json.dumps(decoded, ensure_ascii=False, indent=2)
        print("\n=== Decoded Payload (truncated) ===")
        print(text[:5000])

    return 0


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main(sys.argv[1:]))
