"""Deterministic pest hints derived from NPMS observations."""

from __future__ import annotations

from typing import Iterable

from src.services.aggregation.models import PestObservation

TARGET_METRIC_CODE = "SS0127"  # 복숭아순나방(트랩당마리수)
PEACH_MOTH_THRESHOLD = 10.0


def compute_pest_hints(observations: Iterable[PestObservation]) -> list[str]:
    """Return advisory hints based on NPMS observation metrics."""
    hints: list[str] = []

    for obs in observations:
        if obs.code != TARGET_METRIC_CODE:
            continue
        if obs.value is None or obs.value < PEACH_MOTH_THRESHOLD:
            continue

        area = obs.area or "안동시"
        value_str = f"{obs.value:.2f}".rstrip("0").rstrip(".")
        hints.append(
            f"{area} 복숭아순나방(트랩당마리수) {value_str}마리 관측 — 10마리 이상으로 높음. "
            "살충제 방제 검토를 권장합니다 (출처: NPMS SVC53)."
        )

    return hints


__all__ = ["compute_pest_hints"]
