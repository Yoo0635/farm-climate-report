#!/usr/bin/env python3
"""One-off helpers to exercise the external KMA and NPMS APIs.

The script prints raw JSON responses (pretty formatted) so contributors can
inspect the payloads that the aggregation fetchers are expected to parse.
"""

from __future__ import annotations

import argparse
import json
import sys
import os
from dataclasses import dataclass
from datetime import datetime, time, timedelta
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
    kma_key: str | None
    kma_reg_id: str
    npms_key: str | None
    npms_crop_code: str
    tmfc: str | None = None


def _latest_tmfc(now: datetime | None = None) -> str:
    """Return the latest available tmFc (publication time) in YYYYMMDDHHMM."""
    now = now or datetime.now(tz=KST)
    candidates: set[datetime] = set()
    for day_offset in range(0, 3):
        day = now.date() - timedelta(days=day_offset)
        for hour in (18, 6):
            candidate = datetime.combine(day, time(hour=hour), tzinfo=KST)
            if candidate <= now + timedelta(hours=1):
                candidates.add(candidate)
    if not candidates:
        raise RuntimeError("No publication timestamps derived for tmFc.")
    return max(candidates).strftime("%Y%m%d%H%M")


def fetch_kma(config: ProbeConfig) -> dict[str, Any]:
    if not config.kma_key:
        raise RuntimeError("KMA key is missing. Set KMA_API_KEY (or pass --kma-key).")
    params = {
        "authKey": config.kma_key,
        "dataType": "JSON",
        "pageNo": "1",
        "numOfRows": "50",
        "regId": config.kma_reg_id,
        "tmFc": config.tmfc or _latest_tmfc(),
    }
    url = "https://apihub.kma.go.kr/api/typ02/openApi/MidFcstInfoService/getMidLandFcst"
    request_url = f"{url}?{urlencode(params)}"
    with urlopen(request_url, timeout=20) as response:  # noqa: S310 - trusted hostname
        charset = response.headers.get_content_charset() or "utf-8"
        content = response.read().decode(charset)
        return json.loads(content)


def fetch_npms(config: ProbeConfig) -> dict[str, Any]:
    if not config.npms_key:
        raise RuntimeError("NPMS key is missing. Set NPMS_API_KEY (or pass --npms-key).")
    params = {
        "apiKey": config.npms_key,
        "serviceCode": "SVC31",
        "proxyUrl": "http://example.com/callback",
        "div_id": "result",
        "cropList": config.npms_crop_code,
    }
    url = "http://ncpms.rda.go.kr/npmsAPI/service"
    request_url = f"{url}?{urlencode(params)}"
    with urlopen(request_url, timeout=20) as response:  # noqa: S310 - trusted hostname
        charset = response.headers.get_content_charset() or "utf-8"
        content = response.read().decode(charset)
        return json.loads(content)


def decode_npms_text(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a deep-ish copy with percent-encoding & HTML entities decoded."""
    def _decode(value: Any) -> Any:
        if isinstance(value, str):
            return unescape(unquote(value))
        if isinstance(value, list):
            return [_decode(item) for item in value]
        if isinstance(value, dict):
            return {key: _decode(val) for key, val in value.items()}
        return value

    return _decode(payload)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Fetch sample responses from KMA and NPMS APIs.")
    parser.add_argument("--kma-key", help="KMA API Hub key (MidFcstInfoService). Defaults to KMA_API_KEY env.")
    parser.add_argument("--kma-region", default="11B00000", help="KMA mid-term region code (default: 11B00000)")
    parser.add_argument("--npms-key", help="NPMS API key (SVC31). Defaults to NPMS_API_KEY env.")
    parser.add_argument("--npms-crop", default="FT010601", help="NPMS crop code (default: FT010601 — 사과)")
    parser.add_argument("--tmfc", help="Optional tmFc (YYYYMMDDHHMM). Defaults to latest available publication.")
    args = parser.parse_args(argv)

    # Load .env automatically if available
    if load_dotenv is not None:
        load_dotenv()

    kma_key = args.kma_key or os.environ.get("KMA_API_KEY") or os.environ.get("KMA_AUTH_KEY") or os.environ.get("KMA_SERVICE_KEY")
    npms_key = args.npms_key or os.environ.get("NPMS_API_KEY")

    config = ProbeConfig(
        kma_key=kma_key,
        kma_reg_id=args.kma_region,
        npms_key=npms_key,
        npms_crop_code=args.npms_crop,
        tmfc=args.tmfc,
    )

    print("=== KMA Mid Land Forecast ===")
    try:
        kma_data = fetch_kma(config)
        print(json.dumps(kma_data, ensure_ascii=False, indent=2))
    except Exception as exc:  # noqa: BLE001 - console tool, print error
        print(f"[ERROR] KMA fetch failed: {exc}", file=sys.stderr)

    print("\n=== NPMS SVC31 ===")
    try:
        raw = fetch_npms(config)
        decoded = decode_npms_text(raw)
        print("Raw:")
        print(json.dumps(raw, ensure_ascii=False, indent=2)[:5000])
        print("\nDecoded (truncated to 5000 chars):")
        print(json.dumps(decoded, ensure_ascii=False, indent=2)[:5000])
    except Exception as exc:  # noqa: BLE001 - console tool, print error
        print(f"[ERROR] NPMS fetch failed: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main(sys.argv[1:]))
