"""Helpers to keep Korean messaging concise and readable."""

from __future__ import annotations

import textwrap

MAX_SENTENCE_LENGTH = 40  # characters
SENTENCE_TERMINATORS = ".!?…"  # Simple heuristics for sentence endings


def split_sentences(text: str) -> list[str]:
    """Split text into trimmed sentences using simple punctuation heuristics."""
    sentences: list[str] = []
    buffer: list[str] = []
    for char in text:
        buffer.append(char)
        if char in SENTENCE_TERMINATORS:
            sentence = "".join(buffer).strip()
            if sentence and not all(ch in SENTENCE_TERMINATORS for ch in sentence):
                sentences.append(sentence)
            buffer.clear()
    if buffer:
        sentences.append("".join(buffer).strip())
    return [s for s in sentences if s]


def clamp_sentence_length(sentence: str) -> str:
    """Clip sentence length and append ellipsis if needed."""
    if len(sentence) <= MAX_SENTENCE_LENGTH:
        return sentence
    return textwrap.shorten(sentence, width=MAX_SENTENCE_LENGTH, placeholder="…")


def format_for_sms(text: str) -> str:
    """Return SMS-friendly Korean sentences."""
    sentences = split_sentences(text)
    if not sentences:
        return clamp_sentence_length(text.strip())
    formatted = [clamp_sentence_length(s) for s in sentences]
    return "\n".join(f"• {line}" for line in formatted)


__all__ = ["format_for_sms"]
