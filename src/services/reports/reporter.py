"""Evidence-based report generator using only LLM-1, with file logging.

Creates a prompt from the Evidence Pack and invokes the primary LLM.
Writes `prompt.txt` and `llm1_output.txt` under a per-run directory.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4
from datetime import datetime

from src.services.aggregation.aggregator import get_aggregation_service
from src.services.aggregation.models import AggregateEvidencePack, AggregateRequest
from src.services.reports.prompt import build_evidence_prompt
from src.services.llm.factory import build_llm_stack


@dataclass(slots=True)
class ReportResult:
    issued_at: datetime
    detailed_report: str
    prompt_path: str
    output_path: str


class EvidenceReporter:
    def __init__(self, logs_dir: str | None = None) -> None:
        self._service = get_aggregation_service()
        self._logs_dir = Path(logs_dir or os.environ.get("REPORTS_LOG_DIR", ".reports"))
        self._logs_dir.mkdir(parents=True, exist_ok=True)
        # Build only the primary LLM
        primary, _ = build_llm_stack()
        self._llm_primary = primary

    async def generate(self, payload: AggregateRequest) -> ReportResult:
        pack = await self._service.aggregate(payload)
        prompt = build_evidence_prompt(pack)
        run_dir = self._create_run_dir(pack)
        prompt_path = run_dir / "prompt.txt"
        output_path = run_dir / "llm1_output.txt"
        prompt_path.write_text(prompt)

        # Run LLM-1 in a worker thread to avoid blocking the event loop
        detailed = await asyncio.to_thread(self._llm_primary.generate_report, prompt)
        output_path.write_text(detailed)
        return ReportResult(issued_at=pack.issued_at, detailed_report=detailed, prompt_path=str(prompt_path), output_path=str(output_path))

    def _create_run_dir(self, pack: AggregateEvidencePack) -> Path:
        ts = datetime.now().strftime("%Y%m%dT%H%M%S")
        rid = uuid4().hex[:8]
        region = pack.profile.region.replace(" ", "-").lower()
        crop = pack.profile.crop
        run_dir = self._logs_dir / f"{ts}_{region}_{crop}_{rid}"
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir


__all__ = ["EvidenceReporter", "ReportResult"]

