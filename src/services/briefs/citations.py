"""Inject citation strings into refined content."""

from __future__ import annotations

from typing import Sequence

from src.lib.models import Action


def build_citation_lines(actions: Sequence[Action]) -> list[str]:
    """Create concise citation strings for SMS/detail section."""
    return [f"{action.source_name} ({action.source_year})" for action in actions]


def append_citations(text: str, actions: Sequence[Action]) -> str:
    """Return text unchanged (citations are no longer appended)."""
    return text


__all__ = ["append_citations", "build_citation_lines"]
