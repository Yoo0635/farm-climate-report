"""Utility functions to enforce MVP trust & safety requirements."""

from __future__ import annotations

from typing import Iterable, Protocol


BANNED_KEYWORDS = {"pesticide", "살충제", "약제", "의약", "antibiotic"}


class HasActionFields(Protocol):
    title: str
    source_name: str
    source_year: int | str


def ensure_no_banned_terms(actions: Iterable[HasActionFields]) -> None:
    """Raise ValueError if a banned keyword is present in any action title."""
    for action in actions:
        lower = action.title.lower()
        for keyword in BANNED_KEYWORDS:
            if keyword in lower:
                raise ValueError(f"Banned term detected in action '{action.title}': {keyword}")


def ensure_citations_present(actions: Iterable[HasActionFields]) -> None:
    """Ensure every action contains both source name and year."""
    for action in actions:
        if not action.source_name or not action.source_year:
            raise ValueError(f"Missing citation for action '{action.title}'")


def validate_actions(actions: Iterable[HasActionFields]) -> None:
    """Run all content policy validators."""
    ensure_no_banned_terms(actions)
    ensure_citations_present(actions)


__all__ = ["validate_actions"]
