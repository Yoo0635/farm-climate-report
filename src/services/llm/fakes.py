"""Offline-friendly fake LLM implementations for testing and demos.

These stubs avoid any network/API dependency and return deterministic text
based on inputs so the end-to-end pipeline can be exercised without keys.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from src.services.llm.openai_client import RagContext


@dataclass(slots=True)
class FakeOpenAILLM:
    """Deterministic stand-in for the primary LLM.

    - Echoes context sections and task prompt in a predictable structure.
    - Helps verify prompt wiring and RAG inputs without external calls.
    """

    model: str = "fake-openai"

    def build_prompt(self, context: RagContext, prompt: str) -> str:
        return "\n\n".join([
            "[FAKE-LLM-1] Detailed Report Draft",
            "-- Passages --",
            "\n".join(context.passages) if context.passages else "(none)",
            "-- Web Findings --",
            "\n".join(context.web_findings) if context.web_findings else "(none)",
            "-- Task --",
            prompt,
        ])

    def generate_report(self, context: RagContext, task_prompt: str) -> str:
        # Produce a simple structured draft that looks LLM-like but is deterministic.
        sections: list[str] = [
            "[요약] 2주 행동 보고서(FAKE)",
            "[근거] pass=\"{}\" web=\"{}\"".format(
                min(len(context.passages), 3), min(len(context.web_findings), 3)
            ),
            "[본문]",
            "- 입력 과업: " + task_prompt[:200],
        ]
        # Add at most 3 items from each context section so output is bounded
        for p in list(context.passages)[:3]:
            sections.append("- 로컬: " + p[:140])
        for w in list(context.web_findings)[:3]:
            sections.append("- 웹: " + w[:140])
        return "\n".join(sections)


@dataclass(slots=True)
class FakeGeminiRefiner:
    """Deterministic stand-in for the second LLM refiner.

    - Converts the draft into short bullet-like sentences.
    - Simulates Korean-friendly, concise phrasing.
    """

    model: str = "fake-gemini"
    max_sentences: int = 6

    def build_prompt(self, detailed_report: str) -> str:  # parity with real API
        return detailed_report

    def refine(self, detailed_report: str) -> str:
        # Take first N lines and compress into concise bullets.
        lines: Sequence[str] = [l.strip() for l in detailed_report.splitlines() if l.strip()]
        bullets: list[str] = []
        for line in lines[: self.max_sentences]:
            if not line:
                continue
            # Clamp each bullet to ~40 chars to simulate SMS-friendly output
            bullets.append(("• " + line)[:44])
        return "\n".join(bullets)


__all__ = ["FakeOpenAILLM", "FakeGeminiRefiner"]

