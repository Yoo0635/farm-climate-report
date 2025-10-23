"""Tests for Korean formatting helpers."""

from src.lib.format_ko import format_for_sms, split_sentences


def test_split_sentences_does_not_split_on_da_without_punctuation() -> None:
    text = "이것은 다르다 그러나 계속한다."
    assert split_sentences(text) == [text]


def test_split_sentences_respects_punctuation_endings() -> None:
    text = "첫 문장입니다. 다음 문장입니다!"
    assert split_sentences(text) == ["첫 문장입니다.", "다음 문장입니다!"]


def test_split_sentences_ignores_repeated_periods() -> None:
    text = "감사합니다... 다음 단계로 진행합니다."
    assert split_sentences(text) == ["감사합니다.", "다음 단계로 진행합니다."]


def test_format_for_sms_outputs_bulleted_lines() -> None:
    text = "첫 문장입니다. 다음 문장입니다!"
    assert format_for_sms(text) == "• 첫 문장입니다.\n• 다음 문장입니다!"
