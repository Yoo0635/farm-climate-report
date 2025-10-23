"""LLM-1 client using OpenAI for detailed report generation with RAG context."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Sequence

from openai import OpenAI


DEFAULT_MODEL = "gpt-4.1-mini"


@dataclass(slots=True)
class RagContext:
    """Structured context returned from the vector store + search tools."""

    passages: Sequence[str]
    web_findings: Sequence[str]

    def to_prompt_snippet(self) -> str:
        """Convert context into a formatted prompt segment."""
        sections: list[str] = []
        if self.passages:
            sections.append("### Repository Notes\n" + "\n".join(self.passages))
        if self.web_findings:
            sections.append("### External Findings\n" + "\n".join(self.web_findings))
        return "\n\n".join(sections)


class OpenAILLM:
    """Wrapper around the OpenAI client for the first LLM pass."""

    def __init__(self, model: str | None = None, client: OpenAI | None = None) -> None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAILLM")
        self._model = model or DEFAULT_MODEL
        self._client = client or OpenAI(api_key=api_key)

    def build_prompt(self, context: RagContext, prompt: str) -> str:
        """Compose the final prompt for the detailed report."""
        return "\n\n".join(
            [
                "You are generating a detailed 2-week farm action report for internal use before simplification.",
                "Use the provided climate and pest/disease context, cite sources with year, and produce structured paragraphs.",
                context.to_prompt_snippet(),
                "### Task",
                prompt,
            ]
        )

    def generate_report(self, context: RagContext, task_prompt: str) -> str:
        """Call OpenAI to produce the detailed report."""
        completion = self._client.responses.create(
            model=self._model,
            input=self.build_prompt(context, task_prompt),
        )
        # The new Responses API returns a list of output choices; we grab the first message text.
        return completion.output[0].content[0].text.strip()


__all__ = ["OpenAILLM", "RagContext"]
