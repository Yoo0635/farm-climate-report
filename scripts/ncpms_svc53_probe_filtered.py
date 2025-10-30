#!/usr/bin/env python3
"""List non-zero NPMS SVC53 observations for Andong-si apples."""

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

BASE_URL = "http://ncpms.rda.go.kr/npmsAPI/service"
DEFAULT_INSECT_KEY = os.environ.get("NPMS_DEFAULT_INSECT_KEY", "202500209FT01060101322008")
DEFAULT_SIDO = os.environ.get("NPMS_DEFAULT_SIDO", "47")
TARGET_SIGUNGU_NAME = os.environ.get("NPMS_TARGET_SIGUNGU", "안동시")
TARGET_SIGUNGU_CODE = os.environ.get("NPMS_TARGET_SIGUNGU_CODE", "4717")


def build_request(api_key: str, insect_key: str, sido_code: str, *, service_type: str = "AA003") -> tuple[str, dict[str, str]]:
    params = {
        "apiKey": api_key,
        "serviceCode": "SVC53",
        "serviceType": service_type,
        "insectKey": insect_key,
        "sidoCode": sido_code,
    }
    return BASE_URL, params


def fetch(base_url: str, params: dict[str, str]) -> tuple[str, bytes]:
    url = f"{base_url}?{urlencode(params)}"
    with urlopen(url, timeout=20) as resp:  # noqa: S310 - trusted host
        ctype = resp.headers.get("Content-Type", "application/octet-stream")
        data = resp.read()
        return ctype, data


def print_curl(base_url: str, params: dict[str, str]) -> None:
    print("=== Curl (NPMS SVC53 Filtered) ===")
    print("curl -G --compressed \\")
    print(f"  {shlex.quote(base_url)} \\")
    items = list(params.items())
    for idx, (key, value) in enumerate(items):
        rendered = "${NPMS_API_KEY}" if key == "apiKey" else value
        suffix = "" if idx == len(items) - 1 else " \\"
        print(f"  --data-urlencode {shlex.quote(f'{key}={rendered}')}{suffix}")


def _filter_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    service = payload.get("service") or {}
    entries = service.get("structList") or []
    if isinstance(entries, dict):
        entries = [entries]

    results: list[dict[str, Any]] = []
    for entry in entries:
        sigungu_nm = str(entry.get("sigunguNm") or "")
        sigungu_code = str(entry.get("sigunguCode") or "")
        if TARGET_SIGUNGU_NAME not in sigungu_nm and sigungu_code != TARGET_SIGUNGU_CODE:
            continue

        raw_value = entry.get("inqireValue")
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        if value == 0.0:
            continue

        results.append(
            {
                "area": sigungu_nm,
                "code": entry.get("inqireCnClCode"),
                "pest": entry.get("dbyhsNm"),
                "value": value,
            }
        )

    return results


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Show non-zero Andong-si SVC53 observations")
    parser.add_argument("--npms-key", help="NPMS API key (defaults to NPMS_API_KEY env).")
    parser.add_argument("--insect-key", default=DEFAULT_INSECT_KEY, help="SVC53 insectKey (default: 2025 관찰포 8차).")
    parser.add_argument("--sido-code", default=DEFAULT_SIDO, help="시도코드 (default: 47 — 경북).")
    parser.add_argument("--service-type", default=os.environ.get("NPMS_SVC53_TYPE", "AA003"), choices=["AA001", "AA003"], help="응답 형식: AA003(JSON) / AA001(XML)")
    parser.add_argument("--show-curl", action="store_true", help="Print curl command before request.")
    parser.add_argument("--raw", action="store_true", help="Print raw JSON in addition to filtered output.")
    args = parser.parse_args(argv)

    if load_dotenv is not None:
        load_dotenv()

    api_key = args.npms_key or os.environ.get("NPMS_API_KEY")
    if not api_key:
        print("NPMS key missing. Export NPMS_API_KEY or pass --npms-key.", file=sys.stderr)
        return 1

    base_url, params = build_request(api_key, args.insect_key, args.sido_code, service_type=args.service_type)

    if args.show_curl:
        print_curl(base_url, params)

    try:
        content_type, body = fetch(base_url, params)
    except Exception as exc:  # noqa: BLE001 - CLI helper
        print(f"Request failed: {exc}", file=sys.stderr)
        return 2

    text = body.decode("utf-8", errors="replace")
    if args.raw:
        print(text[:5000])

    if args.service_type != "AA003":
        print("Filtering requires JSON (AA003).")
        return 0

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        print(f"Failed to parse JSON: {exc}", file=sys.stderr)
        return 3

    records = _filter_entries(payload)
    if not records:
        print(f"No non-zero observations for {TARGET_SIGUNGU_NAME} ({TARGET_SIGUNGU_CODE}).")
        return 0

    print(f"=== Non-zero observations for {TARGET_SIGUNGU_NAME} ({TARGET_SIGUNGU_CODE}) ===")
    for idx, record in enumerate(records, start=1):
        print(f"{idx}. {record['pest']} [{record['code']}] = {record['value']} (area: {record['area']})")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
