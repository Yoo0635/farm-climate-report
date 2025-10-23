"""Summaries for keyword replies."""

from __future__ import annotations

from src.services.store.memory_store import StoredBrief


def summarize_brief(stored: StoredBrief) -> str:
    """Create concise summary for REPORT keyword."""
    actions = stored.brief.actions[:3]
    bullets = [f"• {action.title} ({action.timing_window})" for action in actions]
    return "\n".join(
        [
            "최근 브리프 요약:",
            stored.brief.date_range,
            *bullets,
        ]
    )


__all__ = ["summarize_brief"]
