"""Factory helpers to assemble the LLM stack based on environment.

- When `LLM_OFFLINE` or `LLM_MODE=fake`, builds fake clients requiring no keys.
- Otherwise, builds real clients and raises if required keys are missing.
"""

from __future__ import annotations

import os
from typing import Tuple

from src.services.llm.fakes import FakeGeminiRefiner, FakeOpenAILLM
from src.services.llm.gemini_client import GeminiRefiner
from src.services.llm.openai_client import OpenAILLM


def _offline_enabled() -> bool:
    if os.environ.get("LLM_OFFLINE", "").lower() in {"1", "true", "yes"}:
        return True
    if os.environ.get("LLM_MODE", "").lower() == "fake":
        return True
    return False


def build_llm_stack() -> Tuple[object, object]:
    """Return (llm_primary, llm_refiner) according to env flags.

    - Offline/fake: returns FakeOpenAILLM, FakeGeminiRefiner
    - Default: returns OpenAILLM, GeminiRefiner
    """
    if _offline_enabled():
        return FakeOpenAILLM(), FakeGeminiRefiner()
    return OpenAILLM(), GeminiRefiner()


__all__ = ["build_llm_stack"]
