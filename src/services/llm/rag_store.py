"""Lightweight RAG store abstraction for combining local and external context."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import json


@dataclass(slots=True)
class RagResult:
    """Aggregated context for LLM-1."""

    passages: Sequence[str]
    web_findings: Sequence[str]


class RagStore:
    """Simple vector/file search placeholder for the hackathon MVP."""

    def __init__(self, knowledge_dir: Path | None = None) -> None:
        self._knowledge_dir = knowledge_dir or Path("knowledge")

    def _load_local_passages(self, topic: str) -> list[str]:
        """Return local passages related to a topic (stub implementation)."""
        candidates: list[str] = []
        if not self._knowledge_dir.exists():
            return candidates
        for path in self._knowledge_dir.glob("*.jsonl"):
            with path.open("r", encoding="utf-8") as file:
                for line in file:
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if topic in record.get("tags", []):
                        candidates.append(record.get("content", ""))
        return candidates

    def _web_search(self, topic: str) -> list[str]:
        """Placeholder for web search API integration."""
        # Hackathon scope: we return structured placeholders to satisfy LLM prompt.
        return [f"[WebSearch Placeholder] {topic} 관련 최신 자료 (연도 기재 필요)."]

    def fetch(self, topics: Iterable[str]) -> RagResult:
        """Gather context for the provided topics."""
        passages: list[str] = []
        web_findings: list[str] = []
        for topic in topics:
            passages.extend(self._load_local_passages(topic))
            web_findings.extend(self._web_search(topic))
        return RagResult(passages=passages, web_findings=web_findings)


__all__ = ["RagStore", "RagResult"]
