"""LLM-2 client built on Google Gemini for Korean-friendly refinement."""

from __future__ import annotations

import os
from dataclasses import dataclass

from google import genai


DEFAULT_MODEL = "gemini-flash-lite-latest"


@dataclass(slots=True)
class RefinementConfig:
    """Configuration for refinement behaviour."""

    max_sentences: int = 6
    tone: str = "senior-friendly"


class GeminiRefiner:
    """Wrapper for Gemini to simplify detailed reports into SMS-ready sentences."""

    def __init__(self, model: str | None = None, config: RefinementConfig | None = None) -> None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for GeminiRefiner")
        self._client = genai.Client(api_key=api_key)
        self._model_name = model or DEFAULT_MODEL
        self._config = config or RefinementConfig()

    def build_prompt(self, detailed_report: str) -> str:
        """Construct the prompt for Gemini refinement."""
        return (
            "다음 보고서를 한국어로 짧고 이해하기 쉬운 문장으로 정리해 주세요.\n"
            "조건:\n"
            f"- 최대 {self._config.max_sentences}문장\n"
            "- 각 문장은 40자 내외, 간결한 표현\n"
            "- 음성 톤: 친절하고 또박또박 안내하는 농촌 상담원\n"
            "- 날짜/트리거, 행동 3개, 근거(출처+연도) 포함\n\n"
            "=== 보고서 원문 ===\n"
            f"{detailed_report}\n"
        )

    def refine(self, detailed_report: str) -> str:
        """Generate the simplified output."""
        prompt = self.build_prompt(detailed_report)
        response = self._client.models.generate_content(
            model=self._model_name,
            contents=prompt
        )
        return response.text.strip()


__all__ = ["GeminiRefiner", "RefinementConfig"]
