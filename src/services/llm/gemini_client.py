"""LLM-2 client built on Google Gemini for Korean-friendly refinement."""

from __future__ import annotations

import os
from dataclasses import dataclass

from google import genai


DEFAULT_MODEL = "gemini-2.5-pro"


@dataclass(slots=True)
class RefinementConfig:
    """Configuration for refinement behaviour."""

    max_sentences: int = 6
    tone: str = "senior-friendly"


class GeminiRefiner:
    """Wrapper for Gemini to simplify detailed reports into SMS-ready sentences."""

    def __init__(
        self, model: str | None = None, config: RefinementConfig | None = None
    ) -> None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for GeminiRefiner")
        self._client = genai.Client(api_key=api_key)
        self._model_name = model or DEFAULT_MODEL
        self._config = config or RefinementConfig()

    def build_prompt(self, detailed_report: str) -> str:
        """Construct the prompt for Gemini refinement."""
        return (
            "당신은 농업 전문가로서, 이 보고서 내용을 현장의 농업인에게 전달하려고 합니다. 아래 보고서를 분석해서, 농장주가 향후 2주간 가장 시급하게 대응해야 할 사항을 중심으로 요약해 주세요. 최대한 간결하게 필요한 내용만 총 130자 내로 작성해주세요.\n"
            "조건:\n"
            f"- 대상: 농사일로 바쁜 농장주가 쉽게 이해할 수 있도록 작성\n"
            "- 형식: 가장 중요한 순서대로 번호를 매겨 목록으로 정리, 본문만, 마크다운 없이 작성\n"
            "- 내용: 각 항목에 '무엇을(What)', '언제(When)' 해야 하는지 한 문장으로, 간략하게 작성\n"
            "- 언어: 전문 용어 대신 쉽고 간결한 표현 사용, 고유명사는 그대로\n\n"
            "=== 보고서 원문 ===\n"
            f"{detailed_report}\n"
        )

    def refine(self, detailed_report: str) -> str:
        """Generate the simplified output."""
        prompt = self.build_prompt(detailed_report)
        response = self._client.models.generate_content(
            model=self._model_name, contents=prompt
        )
        return response.text.strip()


__all__ = ["GeminiRefiner", "RefinementConfig"]
