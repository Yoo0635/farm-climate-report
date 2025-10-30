#!/usr/bin/env python3
"""Refine an existing LLM-1 output file using LLM-2 and log results.

Usage:
  ./venv/bin/python scripts/refine_from_file.py --input .reports/<run>/llm1_output.txt

Environment:
  - GEMINI_API_KEY for real refinement, or set LLM_OFFLINE=1 for fake refiner.
  - Writes llm2_prompt.txt and llm2_output.txt next to the input file.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

try:
    from dotenv import load_dotenv  # optional
except Exception:  # pragma: no cover
    load_dotenv = None

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.llm.factory import build_llm_stack


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="LLM-2 refinement from existing LLM-1 output file")
    p.add_argument("--input", required=True, help="Path to llm1_output.txt")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    if load_dotenv is not None:
        load_dotenv(ROOT / ".env")

    in_path = Path(args.input).resolve()
    if not in_path.exists():
        print(f"Input file not found: {in_path}")
        return 1

    detailed = in_path.read_text()
    _, refiner = build_llm_stack()
    # refiner may be a fake or real Gemini client
    prompt = refiner.build_prompt(detailed)

    out_dir = in_path.parent
    prompt_path = out_dir / "llm2_prompt.txt"
    output_path = out_dir / "llm2_output.txt"
    prompt_path.write_text(prompt)

    refined = refiner.refine(detailed)
    output_path.write_text(refined)

    print("=== LLM-2 refinement complete ===")
    print(f"Input:   {in_path}")
    print(f"Prompt:  {prompt_path}")
    print(f"Output:  {output_path}")
    print("Preview:\n" + refined[:400])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

