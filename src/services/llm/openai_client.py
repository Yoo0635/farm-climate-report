"""LLM-1 client using OpenAI for detailed report generation.

Now relies on OpenAI Vector Store (file_search tool) when configured,
and does not require a local RAG context injection.
"""

from __future__ import annotations

import os

from openai import OpenAI

DEFAULT_MODEL = "gpt-4.1-mini"


class OpenAILLM:
    """Wrapper around the OpenAI client for the first LLM pass."""

    def __init__(
        self,
        model: str | None = None,
        client: OpenAI | None = None,
        vector_store_id: str | None = None,
    ) -> None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAILLM")
        self._model = model or DEFAULT_MODEL
        self._client = client or OpenAI(api_key=api_key)
        # Optional OpenAI Vector Store integration for file_search
        self._vector_store_id = vector_store_id or os.environ.get(
            "OPENAI_VECTOR_STORE_ID"
        )

    def build_prompt(self, prompt: str) -> str:
        """Compose the final prompt for the detailed report.

        Context retrieval is handled by OpenAI file_search when a vector store is attached.
        """
        return "\n\n".join(
            [
                "You are generating a detailed 2-week farm action report for internal use before simplification.",
                "Use appropriate climate and pest/disease knowledge, cite sources with year, and produce structured paragraphs.",
                "### Task",
                prompt,
            ]
        )

    def generate_report(self, task_prompt: str) -> str:
        """Call OpenAI to produce the detailed report."""
        create_kwargs: dict = {
            "model": self._model,
            "input": self.build_prompt(task_prompt),
        }
        # If a vector store is configured, enable file_search tool with attachment
        if self._vector_store_id:
            create_kwargs["tools"] = [{"type": "file_search"}]
            create_kwargs["attachments"] = [
                {
                    "vector_store_id": self._vector_store_id,
                }
            ]

        completion = self._client.responses.create(**create_kwargs)
        # The new Responses API returns a list of output choices; we grab the first message text.
        return completion.output[0].content[0].text.strip()


__all__ = ["OpenAILLM"]
