"""Helpers for light formatting of SMS-ready Korean text."""

from __future__ import annotations


def format_for_sms(text: str) -> str:
    """Return SMS-friendly text without additional bullets or truncation."""
    if not text:
        return ""
    # Normalize whitespace per line but keep author-provided structure intact.
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(lines).strip()


__all__ = ["format_for_sms"]
