#!/usr/bin/env python3
"""Generate a detailed report from the Evidence Pack using LLM-1 only.

- Loads keys from .env
- Calls aggregator (demo by default) and LLM-1
- Writes prompt/output files and prints their paths + a short preview
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
import os
import sys

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.aggregation.models import AggregateRequest
from src.services.reports.reporter import EvidenceReporter


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evidence → LLM-1 report probe (Andong-si · Apple)")
    p.add_argument("--demo", action="store_true", help="Use demo evidence instead of live fetch")
    p.add_argument("--region", default="Andong-si")
    p.add_argument("--crop", default="apple")
    p.add_argument("--stage", default="flowering")
    p.add_argument("--refine", action="store_true", help="Run LLM-2 refinement and log its prompt/output")
    return p.parse_args(argv)


async def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    if load_dotenv is not None:
        load_dotenv(ROOT / ".env")

    reporter = EvidenceReporter()
    req = AggregateRequest(region=args.region, crop=args.crop, stage=args.stage, demo=bool(args.demo))
    result = await reporter.generate(req, refine=bool(args.refine))

    print("=== Evidence → LLM-1 Report ===")
    print(f"Issued: {result.issued_at}")
    print(f"Prompt file: {result.prompt_path}")
    print(f"Output file: {result.output_path}")
    if args.refine and result.refined_report:
        print(f"LLM-2 prompt file: {result.llm2_prompt_path}")
        print(f"LLM-2 output file: {result.llm2_output_path}")
    print("\n--- Report Preview (first 600 chars) ---")
    print(result.detailed_report[:600])
    if args.refine and result.refined_report:
        print("\n--- Refined Preview (first 400 chars) ---")
        print(result.refined_report[:400])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
