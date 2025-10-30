#!/usr/bin/env python3
"""Probe NPMS SVC53 (병해충예찰검색) with explicit params.

Usage examples:
  export NPMS_API_KEY=...  # required
  python3 scripts/ncpms_svc53_probe.py --insect-key 1000000044 --sido-code 47 --show-curl --raw

Notes:
  - This endpoint requires a valid `insectKey` (상세조회키) and a `sidoCode` (시도코드).
  - If you don't know the exact keys, please provide them; otherwise the API may return ERR_901.
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


def build_request(api_key: str, insect_key: str, sido_code: str, *, service_type: str = "AA003", base_url: str = "http://ncpms.rda.go.kr/npmsAPI/service") -> tuple[str, dict[str, str]]:
    params = {
        "apiKey": api_key,
        "serviceCode": "SVC53",
        "serviceType": service_type,  # AA003: JSON, AA001: XML
        "insectKey": insect_key,
        "sidoCode": sido_code,
    }
    return base_url, params


def fetch(base_url: str, params: dict[str, str]) -> tuple[str, bytes]:
    """Return content-type and raw bytes."""
    url = f"{base_url}?{urlencode(params)}"
    with urlopen(url, timeout=20) as resp:  # noqa: S310 - trusted host
        ctype = resp.headers.get("Content-Type", "application/octet-stream")
        data = resp.read()
        return ctype, data


def print_curl(base_url: str, params: dict[str, str]) -> None:
    print("=== Curl (NPMS SVC53) ===")
    print("curl -G --compressed \\")
    print(f"  {shlex.quote(base_url)} \\")
    items = list(params.items())
    for i, (k, v) in enumerate(items):
        rendered = "${NPMS_API_KEY}" if k == "apiKey" else v
        suffix = "" if i == len(items) - 1 else " \\"
        print(f"  --data-urlencode {shlex.quote(f'{k}={rendered}')}" + suffix)


def _summarize_service(payload: dict[str, Any], *, sigungu_filter: str | None) -> None:
    service = payload.get("service") or {}
    predict_code = service.get("predictnSpchcknCode")
    predict_name = service.get("predictnSpchcknNm")
    crop_name = service.get("kncrNm")
    exam_code = service.get("examinSpchcknCode")
    exam_name = service.get("examinSpchcknNm")
    tmrd = service.get("examinTmrd")

    header_parts = []
    if crop_name:
        header_parts.append(f"crop={crop_name}")
    if predict_name:
        header_parts.append(f"predict={predict_name}({predict_code})")
    if exam_name:
        header_parts.append(f"exam={exam_name}({exam_code}) tmrd={tmrd}")
    print(" ; ".join(header_parts) or "(no header data)")

    entries = service.get("structList") or []
    if isinstance(entries, dict):
        entries = [entries]

    if sigungu_filter:
        sigungu_filter = sigungu_filter.strip()
        entries = [item for item in entries if item.get("sigunguNm") and sigungu_filter in item["sigunguNm"]]

    if not entries:
        print("No records matched the filters.")
        return

    for idx, item in enumerate(entries, start=1):
        sigungu_nm = item.get("sigunguNm")
        sigungu_code = item.get("sigunguCode")
        pest_name = item.get("dbyhsNm")
        value = item.get("inqireValue")
        detail = item.get("inqireCnClCode")
        print(f"{idx}. {sigungu_nm}({sigungu_code}) — {pest_name} [{detail}] value={value}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Probe NPMS SVC53 (예찰검색)")
    parser.add_argument("--npms-key", help="NPMS API key (defaults to NPMS_API_KEY env).")
    parser.add_argument("--insect-key", default=os.environ.get("NPMS_DEFAULT_INSECT_KEY"), help="SVC53 insectKey (상세조회키).")
    parser.add_argument("--sido-code", default=os.environ.get("NPMS_DEFAULT_SIDO"), help="시도코드 (예: 경북=47).")
    parser.add_argument("--service-type", default=os.environ.get("NPMS_SVC53_TYPE", "AA003"), choices=["AA001", "AA003"], help="응답 형식: AA003(JSON) / AA001(XML)")
    parser.add_argument("--show-curl", action="store_true", help="Print a sanitized curl command before request.")
    parser.add_argument("--sigungu", help="Filter results to rows whose sigunguNm contains this text.")
    parser.add_argument("--raw", action="store_true", help="Print raw response body (truncated).")
    args = parser.parse_args(argv)

    if load_dotenv is not None:
        load_dotenv()

    api_key = args.npms_key or os.environ.get("NPMS_API_KEY")
    if not api_key:
        print("NPMS key missing. Export NPMS_API_KEY or pass --npms-key.", file=sys.stderr)
        return 1
    if not args.insect_key or not args.sido_code:
        print("insectKey and sidoCode are required. Pass via flags or env (NPMS_DEFAULT_INSECT_KEY, NPMS_DEFAULT_SIDO).", file=sys.stderr)
        return 2

    base_url, params = build_request(api_key, args.insect_key, args.sido_code, service_type=args.service_type)

    if args.show_curl:
        print_curl(base_url, params)

    try:
        _content_type, body = fetch(base_url, params)
    except Exception as exc:  # noqa: BLE001
        print(f"Request failed: {exc}", file=sys.stderr)
        return 3

    # Try to parse JSON if AA003 requested
    decoded = body.decode("utf-8", errors="replace")
    if args.raw or args.service_type == "AA001":
        if args.raw:
            print(decoded[:5000])
        else:
            print(decoded.splitlines()[0] if decoded else "<empty>")
        return 0

    try:
        parsed = json.loads(decoded)
    except json.JSONDecodeError:
        print(decoded[:5000])
        return 0

    _summarize_service(parsed, sigungu_filter=args.sigungu)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
