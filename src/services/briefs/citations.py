"""Inject citation strings into refined content."""

from __future__ import annotations

from typing import Sequence

from src.lib.models import Action


def build_citation_lines(actions: Sequence[Action]) -> list[str]:
    """Create concise citation strings for SMS/detail section."""
    return [f"{action.source_name} ({action.source_year})" for action in actions]


def append_citations(text: str, actions: Sequence[Action]) -> str:
    """Append citation block to text if not already present."""
    citations = build_citation_lines(actions)
    if not citations:
        return text
    citation_block = " / ".join(dict.fromkeys(citations))  # preserve order, unique
    if citation_block in text:
        return text
    return f"{text}\n근거: {citation_block}"


__all__ = ["append_citations", "build_citation_lines"]
