"""Generate personalized brief content using the evidence-backed pipeline."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Sequence

from src.lib.models import Action, Profile, Signal
from src.services.aggregation.models import AggregateRequest
from src.services.llm.factory import build_llm_stack
from src.services.llm.gemini_client import GeminiRefiner
from src.services.llm.openai_client import OpenAILLM
from src.services.reports.reporter import EvidenceReporter, ReportResult

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class BriefGenerationContext:
    """Inputs required to build a 2-week brief."""

    profile: Profile
    signals: Sequence[Signal]
    actions: Sequence[Action]
    date_range: str


@dataclass(slots=True)
class BriefGenerationResult:
    """Outputs from the generation pipeline."""

    detailed_report: str
    refined_report: str
    prompt_path: str | None = None
    output_path: str | None = None
    llm2_prompt_path: str | None = None
    llm2_output_path: str | None = None


class BriefGenerator:
    """Coordinates aggregation, LLM-1, and LLM-2 to produce brief content."""

    def __init__(
        self,
        llm_primary: OpenAILLM | None = None,
        llm_refiner: GeminiRefiner | None = None,
        reporter: EvidenceReporter | None = None,
    ) -> None:
        primary, refiner = build_llm_stack()
        self._llm_primary = llm_primary or primary  # type: ignore[assignment]
        self._llm_refiner = llm_refiner or refiner  # type: ignore[assignment]
        self._reporter = reporter or EvidenceReporter()

    def generate(self, context: BriefGenerationContext) -> BriefGenerationResult:
        """Run pipeline and return raw outputs; downstream components format SMS/detail page."""
        evidence_report = self._generate_with_evidence(context)
        if evidence_report is not None:
            detailed = evidence_report.detailed_report
            refined = evidence_report.refined_report or self._llm_refiner.refine(detailed)
            return BriefGenerationResult(
                detailed_report=detailed,
                refined_report=refined,
                prompt_path=evidence_report.prompt_path,
                output_path=evidence_report.output_path,
                llm2_prompt_path=evidence_report.llm2_prompt_path,
                llm2_output_path=evidence_report.llm2_output_path,
            )

        logger.debug(
            "Evidence-based generation unavailable; falling back to legacy prompt (%s/%s)",
            context.profile.region,
            context.profile.crop,
        )
        detailed_prompt = self._build_legacy_prompt(context)
        detailed_report = self._llm_primary.generate_report(detailed_prompt)
        refined = self._llm_refiner.refine(detailed_report)
        return BriefGenerationResult(detailed_report=detailed_report, refined_report=refined)

    def _generate_with_evidence(self, context: BriefGenerationContext) -> ReportResult | None:
        """Attempt to use the EvidenceReporter; return None if unsupported or unavailable."""
        request = AggregateRequest(
            region=context.profile.region,
            crop=context.profile.crop,
            stage=context.profile.stage,
        )

        try:
            return asyncio.run(self._reporter.generate(request, refine=True))
        except ValueError as exc:
            if "Unsupported region/crop" in str(exc):
                logger.debug("Evidence reporter skipped: %s", exc)
                return None
            logger.warning("Evidence reporter failed with ValueError: %s", exc)
            return None
        except Exception as exc:  # noqa: BLE001
            logger.warning("Evidence reporter failed; falling back to legacy prompt: %s", exc)
            return None

    def _build_legacy_prompt(self, context: BriefGenerationContext) -> str:
        action_summary = "\n".join(
            f"- {action.title} (시기: {action.timing_window}, 트리거: {action.trigger})"
            for action in context.actions
        )
        signal_summary = "\n".join(
            f"- {signal.code} ({signal.type}): {signal.severity or '중요'}"
            for signal in context.signals
        )
        return (
            f"지역: {context.profile.region}\n"
            f"작물: {context.profile.crop} / 생육 단계: {context.profile.stage}\n"
            f"기간: {context.date_range}\n\n"
            "## 기후/병해충 신호\n"
            f"{signal_summary}\n\n"
            "## 예정된 행동 (초안)\n"
            f"{action_summary}\n\n"
            "각 행동은 출처와 연도를 명시해야 하며, Plan B와 체크리스트를 포함한 상세 보고서를 작성해 주세요."
        )


__all__ = ["BriefGenerator", "BriefGenerationContext", "BriefGenerationResult"]
