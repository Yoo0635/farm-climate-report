from __future__ import annotations

from src.services.aggregation.models import PestObservation
from src.services.aggregation.pest_hints import compute_pest_hints


def test_compute_pest_hints_triggers_on_threshold() -> None:
    observations = [
        PestObservation(pest="복숭아순나방", metric="트랩당마리수", code="SS0127", value=11.5, area="안동시"),
        PestObservation(pest="사과굴나방", metric="트랩당마리수", code="SS0128", value=5.0, area="안동시"),
    ]

    hints = compute_pest_hints(observations)

    assert hints, "Expected hint when peach moth trap count exceeds threshold"
    assert "복숭아순나방" in hints[0]


def test_compute_pest_hints_ignores_low_values() -> None:
    observations = [
        PestObservation(pest="복숭아순나방", metric="트랩당마리수", code="SS0127", value=3.0, area="안동시"),
    ]

    hints = compute_pest_hints(observations)

    assert hints == []
