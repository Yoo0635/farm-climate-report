"""Generate personalized brief content using the two-step LLM pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from src.lib.models import Action, Profile, Signal
from src.services.llm.gemini_client import GeminiRefiner
from src.services.llm.openai_client import OpenAILLM, RagContext
from src.services.llm.rag_store import RagStore, RagResult


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

    rag_result: RagResult
    detailed_report: str
    refined_report: str


class BriefGenerator:
    """Coordinates RAG, LLM-1, and LLM-2 to produce brief content."""

    def __init__(
        self,
        rag_store: RagStore | None = None,
        llm_primary: OpenAILLM | None = None,
        llm_refiner: GeminiRefiner | None = None,
    ) -> None:
        self._rag_store = rag_store or RagStore()
        self._llm_primary = llm_primary or OpenAILLM()
        self._llm_refiner = llm_refiner or GeminiRefiner()

    def _topics_from_signals(self, signals: Iterable[Signal], profile: Profile) -> list[str]:
        topics = {profile.crop, profile.region, profile.stage}
        for signal in signals:
            topics.add(signal.code)
        return [topic for topic in topics if topic]

    def generate(self, context: BriefGenerationContext) -> BriefGenerationResult:
        """Run pipeline and return raw outputs; downstream components format SMS/detail page."""
        topics = self._topics_from_signals(context.signals, context.profile)
        rag_result = self._rag_store.fetch(topics)
        detailed_prompt = self._build_detailed_prompt(context)
        detailed_report = self._llm_primary.generate_report(
            RagContext(passages=rag_result.passages, web_findings=rag_result.web_findings),
            detailed_prompt,
        )
        refined = self._llm_refiner.refine(detailed_report)
        return BriefGenerationResult(
            rag_result=rag_result,
            detailed_report=detailed_report,
            refined_report=refined,
        )

    def _build_detailed_prompt(self, context: BriefGenerationContext) -> str:
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
