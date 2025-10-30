#!/usr/bin/env python3
"""Probe NPMS SVC51 (병해충예찰검색 목록) to discover insectKey values.

Typical workflow:
    export NPMS_API_KEY=...
    python3 scripts/ncpms_svc51_probe.py --crop FT010601 --year 2025 --show-curl

Use the resulting `insectKey` values with `scripts/ncpms_svc53_probe.py`.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None


def build_request(
    api_key: str,
    *,
    year: str | None,
    predict_code: str | None,
    crop_code: str | None,
    display_count: int,
    start_point: int,
    service_type: str,
    base_url: str = "http://ncpms.rda.go.kr/npmsAPI/service",
) -> tuple[str, dict[str, str]]:
    params: dict[str, str] = {
        "apiKey": api_key,
        "serviceCode": "SVC51",
        "serviceType": service_type,
        "displayCount": str(display_count),
        "startPoint": str(start_point),
    }
    if year:
        params["searchExaminYear"] = year
    if predict_code:
        params["searchPredictnSpchcknCode"] = predict_code
    if crop_code:
        params["searchKncrCode"] = crop_code
    return base_url, params


def fetch(base_url: str, params: dict[str, str]) -> dict[str, Any]:
    url = f"{base_url}?{urlencode(params)}"
    with urlopen(url, timeout=20) as resp:  # noqa: S310 - trusted host
        payload = resp.read().decode("utf-8", errors="replace")
    return json.loads(payload)


def print_curl(base_url: str, params: dict[str, str]) -> None:
    print("=== Curl (NPMS SVC51) ===")
    print("curl -G --compressed \\")
    print(f"  {shlex.quote(base_url)} \\")
    items = list(params.items())
    for idx, (key, value) in enumerate(items):
        rendered = "${NPMS_API_KEY}" if key == "apiKey" else value
        suffix = "" if idx == len(items) - 1 else " \\"
        print(f"  --data-urlencode {shlex.quote(f'{key}={rendered}')}" + suffix)


def summarize(data: dict[str, Any], *, limit: int) -> None:
    service = data.get("service") or {}
    total = service.get("totalCount", 0)
    count = service.get("displayCount", 0)
    start = service.get("startPoint", 0)
    build_time = service.get("buildTime")
    print(
        f"buildTime={build_time} totalCount={total} startPoint={start} displayCount={count}"
    )

    entries = service.get("list") or []
    if isinstance(entries, dict):
        entries = [entries]

    for idx, entry in enumerate(entries[:limit], start=1):
        insect_key = entry.get("insectKey")
        predict_name = entry.get("predictnSpchcknNm")
        predict_code = entry.get("predictnSpchcknCode")
        crop = entry.get("kncrNm")
        crop_code = entry.get("kncrCode")
        exam_name = entry.get("examinSpchcknNm")
        exam_code = entry.get("examinSpchcknCode")
        year = entry.get("examinYear")
        tmrd = entry.get("examinTmrd")
        input_date = entry.get("inputStdrDatetm")
        print(f"{idx}. insectKey={insect_key}")
        print(f"   crop={crop}({crop_code}) predict={predict_name}({predict_code})")
        print(
            f"   exam={exam_name}({exam_code}) year={year} tmrd={tmrd} input={input_date}"
        )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Probe NPMS SVC51 (예찰 목록 조회)")
    parser.add_argument(
        "--npms-key", help="NPMS API key (defaults to NPMS_API_KEY env)."
    )
    parser.add_argument(
        "--year",
        default=os.environ.get("NPMS_SVC51_YEAR"),
        help="조사년도 (기본: 현재년도).",
    )
    parser.add_argument(
        "--predict-code",
        default=os.environ.get("NPMS_DEFAULT_PREDICT_CODE"),
        help="예찰구분코드 (searchPredictnSpchcknCode).",
    )
    parser.add_argument(
        "--crop",
        default=os.environ.get("NPMS_DEFAULT_CROP"),
        help="작물코드 (kncrCode).",
    )
    parser.add_argument(
        "--count", type=int, default=10, help="표시할 결과 개수 (1-50)."
    )
    parser.add_argument("--start", type=int, default=1, help="시작 위치 (1-500).")
    parser.add_argument(
        "--service-type",
        default=os.environ.get("NPMS_SVC51_TYPE", "AA003"),
        choices=["AA001", "AA003"],
        help="응답 형식: AA003(JSON) / AA001(XML).",
    )
    parser.add_argument(
        "--show-curl", action="store_true", help="요청에 사용할 curl 명령을 출력합니다."
    )
    parser.add_argument("--raw", action="store_true", help="JSON 전문을 출력합니다.")
    args = parser.parse_args(argv)

    if load_dotenv is not None:
        load_dotenv()

    api_key = args.npms_key or os.environ.get("NPMS_API_KEY")
    if not api_key:
        print(
            "NPMS key missing. Export NPMS_API_KEY or pass --npms-key.", file=sys.stderr
        )
        return 1

    display_count = max(1, min(args.count, 50))
    start_point = max(1, min(args.start, 500))
    base_url, params = build_request(
        api_key,
        year=args.year,
        predict_code=args.predict_code,
        crop_code=args.crop,
        display_count=display_count,
        start_point=start_point,
        service_type=args.service_type,
    )

    if args.show_curl:
        print_curl(base_url, params)

    try:
        data = fetch(base_url, params)
    except Exception as exc:  # noqa: BLE001
        print(f"Request failed: {exc}", file=sys.stderr)
        return 2

    if args.raw:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    summarize(data, limit=display_count)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main(sys.argv[1:]))
