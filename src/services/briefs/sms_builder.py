"""Utilities for shaping SMS messages from refined report outputs."""

from __future__ import annotations

from textwrap import shorten

from src.lib.format_ko import format_for_sms

LINK_PREFIX = "상세보기:"


def build_sms(refined_text: str, link_url: str | None = None) -> str:
    """Return the final SMS body respecting brevity constraints."""
    content = format_for_sms(refined_text)
    link_line = f"{LINK_PREFIX} {link_url}" if link_url else ""
    combined = f"{content}\n{link_line}".strip()

    if len(combined) > 450:
        content = shorten(content, width=400 if link_line else 450, placeholder="…")
        combined = f"{content}\n{link_line}".strip()

    return combined


__all__ = ["build_sms"]
