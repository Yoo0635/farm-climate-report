#!/usr/bin/env python3
"""CLI runner for the LLM pipeline without SMS sending.

Runs: RAG → LLM‑1 → LLM‑2 → SMS formatting, prints results to console,
and writes a detailed log file.

Usage example:
  python scripts/pipeline_preview.py \
    --region KR/Seoul --crop Strawberry --stage Flowering \
    --offline --log logs/pipeline.log
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _ensure_project_root() -> None:
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))


def _load_pipeline_modules():
    _ensure_project_root()
    from src.lib.models import Profile
    from src.lib.policy import validate_actions
    from src.services.briefs.citations import append_citations
    from src.services.briefs.generator import BriefGenerationContext, BriefGenerator
    from src.services.briefs.sms_builder import build_sms
    from src.services.signals.mappings import default_signals_actions

    return (
        Profile,
        validate_actions,
        append_citations,
        BriefGenerationContext,
        BriefGenerator,
        build_sms,
        default_signals_actions,
    )


def _build_logger(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("pipeline_preview")
    # Capture DEBUG+; handlers control emission to console vs file
    logger.setLevel(logging.DEBUG)
    # Clear existing handlers if re-run in same process
    logger.handlers.clear()

    fmt = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the LLM pipeline without sending SMS."
    )
    parser.add_argument(
        "--region", required=True, help="Region identifier, e.g., KR/Seoul"
    )
    parser.add_argument("--crop", required=True, help="Crop name, e.g., Strawberry")
    parser.add_argument("--stage", required=True, help="Growth stage, e.g., Flowering")
    parser.add_argument(
        "--date-range", dest="date_range", default=None, help="Override date range text"
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        default=False,
        help="Force offline fake LLMs (equivalent to LLM_OFFLINE=1)",
    )
    default_log = (
        Path("logs") / f"pipeline-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}.log"
    )
    parser.add_argument("--log", type=Path, default=default_log, help="Log file path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    load_dotenv(PROJECT_ROOT / ".env")
    (
        Profile,
        validate_actions,
        append_citations,
        BriefGenerationContext,
        BriefGenerator,
        build_sms,
        default_signals_actions,
    ) = _load_pipeline_modules()
    args = parse_args(argv)

    if args.offline:
        os.environ["LLM_OFFLINE"] = "1"

    logger = _build_logger(Path(args.log))

    # Prepare inputs
    profile = Profile(
        id="preview-cli",
        phone="",
        region=args.region,
        crop=args.crop,
        stage=args.stage,
        language="ko",
        opt_in=True,
    )
    signals, actions = default_signals_actions()
    validate_actions(actions)
    now = datetime.now(UTC)
    date_range = (
        args.date_range or f"{now:%Y-%m-%d} ~ {(now + timedelta(days=14)):%Y-%m-%d}"
    )

    logger.info("Starting pipeline preview")
    logger.info(
        "Inputs: region=%s crop=%s stage=%s",
        args.region,
        args.crop,
        args.stage,
    )
    logger.info("Date range: %s", date_range)

    try:
        generator = BriefGenerator()
        gen = generator.generate(
            BriefGenerationContext(
                profile=profile, signals=signals, actions=actions, date_range=date_range
            )
        )
    except Exception as exc:  # noqa: BLE001 - surface for CLI
        logger.error("Pipeline failed: %s", exc)
        return 2

    # Post-processing
    refined_text = append_citations(gen.refined_report, actions)
    base_url = os.environ.get(
        "DETAIL_BASE_URL", "https://parut.com/public/briefs"
    ).rstrip("/")
    sms_body = build_sms(refined_text, link_url=f"{base_url}/preview")

    # Console-friendly output
    print("\n=== Pipeline Preview ===")
    print(f"Region/Crop/Stage: {args.region} / {args.crop} / {args.stage}")
    print("Scenario: n/a (evidence-driven)")
    print(f"Date Range: {date_range}")
    if gen.prompt_path:
        print(f"Prompt file: {gen.prompt_path}")
    if gen.llm2_output_path:
        print(f"LLM-2 output file: {gen.llm2_output_path}")
    print("\n--- Detailed Report (first 600 chars) ---")
    print(gen.detailed_report[:600])
    print("\n--- Refined Report ---")
    print(refined_text)
    print("\n--- SMS Body ---")
    print(sms_body)

    # Log details
    # RAG counts removed: Vector Store file_search is handled by the model
    logger.info("Detailed report length: %d", len(gen.detailed_report))
    logger.debug("Detailed report (full):\n%s", gen.detailed_report)
    logger.info("Refined report length: %d", len(refined_text))
    logger.debug("Refined report (full):\n%s", refined_text)
    logger.info("SMS body length: %d", len(sms_body))
    logger.debug("SMS body (full):\n%s", sms_body)
    if gen.prompt_path:
        logger.info("LLM-1 prompt logged at: %s", gen.prompt_path)
    if gen.llm2_output_path:
        logger.info("LLM-2 output logged at: %s", gen.llm2_output_path)
    logger.info("Completed successfully. Log: %s", str(args.log))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
