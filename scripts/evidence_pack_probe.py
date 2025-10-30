#!/usr/bin/env python3
"""Evidence Pack probe (Andong-si · Apple) with optional raw NPMS text view.

- Loads keys from .env
- Calls the aggregation service (live by default)
- Prints a concise summary and SVC53-style observation list
- Optionally prints raw NPMS SVC31/SVC53 responses without parsing
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import shlex
from pathlib import Path
from urllib.parse import urlencode, unquote
from urllib.request import urlopen
from html import unescape

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.aggregation.aggregator import get_aggregation_service
from src.services.aggregation.models import AggregateRequest


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evidence Pack probe for Andong-si · Apple")
    p.add_argument("--demo", action="store_true", help="Use demo data instead of live fetch")
    p.add_argument("--json", action="store_true", help="Print full Evidence Pack JSON")
    p.add_argument("--top", type=int, default=10, help="Max items to include in trimmed JSON (default: 10)")
    p.add_argument("--observations-only", action="store_true", help="Only print SVC53-style observation list")
    # NPMS raw view (no parsing) helpers
    p.add_argument("--npms-svc53-raw", action="store_true", help="Also print NPMS SVC53 raw body (no parsing)")
    p.add_argument("--npms-svc31-raw", action="store_true", help="Also print NPMS SVC31 raw body (no parsing)")
    p.add_argument("--decode", action="store_true", help="When printing raw NPMS text, percent/HTML-decode it")
    return p.parse_args(argv)


def _print_observation_list(observations: list, *, target_name: str, target_code: str | None = None) -> None:
    print(f"=== Non-zero observations for {target_name} ({target_code or '-'}) ===")
    if not observations:
        print("(none)")
        return
    for idx, o in enumerate(observations, start=1):
        print(f"{idx}. {o.pest} [{o.code}] = {o.value} (area: {o.area})")


def _print_npms_raw(service_code: str, params: dict[str, str], *, base_url: str, decode: bool) -> None:
    title = f"NPMS {service_code} Raw"
    print(f"=== {title} ===")
    parts = [f"--data-urlencode {shlex.quote(f'{k}={("${NPMS_API_KEY}" if k == "apiKey" else v)}')}" for k, v in params.items()]
    print("curl -G --compressed " + base_url + " " + " ".join(parts))
    url = f"{base_url}?{urlencode(params)}"
    try:
        with urlopen(url, timeout=20) as resp:  # noqa: S310
            raw = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        print(f"{service_code} request failed: {exc}")
        return
    text = unescape(unquote(raw)) if decode else raw
    print(text[:5000])


async def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    if load_dotenv is not None:
        load_dotenv(ROOT / ".env")

    missing: list[str] = []
    if not os.environ.get("KMA_API_KEY") and not os.environ.get("KMA_AUTH_KEY") and not os.environ.get("KMA_SERVICE_KEY"):
        missing.append("KMA_API_KEY")
    if not os.environ.get("NPMS_API_KEY"):
        missing.append("NPMS_API_KEY")
    if missing:
        print(f"WARN: missing env keys: {', '.join(missing)} — proceeding; sources without keys are skipped.")

    # Optional NPMS raw text preview (no parsing)
    if args.npms_svc53_raw or args.npms_svc31_raw:
        api_key = os.environ.get("NPMS_API_KEY")
        base_url = os.environ.get("NPMS_API_BASE_URL", "http://ncpms.rda.go.kr/npmsAPI/service")
        if not api_key:
            print("NPMS_API_KEY missing; cannot fetch raw NPMS text.")
        else:
            if args.npms_svc53_raw:
                insect_key = os.environ.get("NPMS_DEFAULT_INSECT_KEY", "202500209FT01060101322008")
                sido = os.environ.get("NPMS_DEFAULT_SIDO", "47")
                svc53_params = {
                    "apiKey": api_key,
                    "serviceCode": "SVC53",
                    "serviceType": os.environ.get("NPMS_SVC53_TYPE", "AA003"),
                    "insectKey": insect_key,
                    "sidoCode": sido,
                }
                _print_npms_raw("SVC53", svc53_params, base_url=base_url, decode=args.decode)

            if args.npms_svc31_raw:
                crop = os.environ.get("NPMS_DEFAULT_CROP", "FT010601")
                svc31_params = {
                    "apiKey": api_key,
                    "serviceCode": "SVC31",
                    "proxyUrl": "https://example.com/callback",
                    "div_id": "result",
                    "cropList": crop,
                }
                _print_npms_raw("SVC31", svc31_params, base_url=base_url, decode=args.decode)

    service = get_aggregation_service()
    req = AggregateRequest(region="Andong-si", crop="apple", stage="flowering", demo=bool(args.demo))
    pack = await service.aggregate(req)

    # Output header and text unless observations-only
    if not args.observations_only:
        print("=== Evidence Pack — Andong-si · Apple ===")
        print(f"Issued: {pack.issued_at}")
        climate = pack.climate
        provenance = ", ".join(climate.provenance) if climate.provenance else "-"
        print(
            f"Climate horizon: D+{climate.horizon_days} · daily={len(climate.daily)} · hourly={len(climate.hourly)} · "
            f"warnings={len(climate.warnings)} · provenance={provenance}"
        )
        print(
            f"Pest data: bulletins={len(pack.pest.bulletins)} · observations={len(pack.pest.observations)} "
            f"· provenance={', '.join(pack.pest.provenance) if pack.pest.provenance else '-'}"
        )
        if pack.pest_hints:
            print("Hints:")
            for h in pack.pest_hints:
                print(f"  - {h}")
        if pack.soft_hints:
            print(
                f"Soft hints: rain_run={pack.soft_hints.rain_run_max_days}d · "
                f"heat_hours={pack.soft_hints.heat_hours_ge_33c} · wet_nights={pack.soft_hints.wet_nights_count}"
            )
        print()
    # Print NPMS SVC53-filtered style text (already formatted in pack.text)
    print(pack.text)

    # Print a trimmed or full JSON view
    if not args.observations_only:
        if args.json:
            print("\n--- Evidence Pack (full JSON) ---")
            print(json.dumps(pack.model_dump(), ensure_ascii=False, indent=2, default=str))
        # no trimmed JSON view needed after refactor
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
