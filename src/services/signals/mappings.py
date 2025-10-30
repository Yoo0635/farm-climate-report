"""Default action/signal scaffolding for brief generation.

These remain lightweight placeholders until evidence-driven
action synthesis is implemented.
"""

from __future__ import annotations

from typing import List, Tuple

from src.lib.models import Action, Signal


def _heatwave_actions() -> List[Action]:
    return [
        Action(
            title="낮 시간 차광막 조정",
            timing_window="당일 11:00 이전",
            trigger="기온 33°C 이상 예보",
            icon=None,
            source_name="농촌진흥청",
            source_year=2024,
        ),
        Action(
            title="미세 관수로 기온 낮추기",
            timing_window="당일 오후",
            trigger="한낮 복사열",
            icon=None,
            source_name="기상청",
            source_year=2023,
        ),
        Action(
            title="과실 그늘 확보",
            timing_window="2일 내",
            trigger="과실 표면 온도 30°C 이상",
            icon=None,
            source_name="서울대 농생대",
            source_year=2022,
        ),
    ]


def default_signals_actions() -> Tuple[List[Signal], List[Action]]:
    """Return generic fallback signals/actions for prompts/citations."""
    signals = [Signal(type="climate", code="GENERAL", severity="정보")]
    return signals, _heatwave_actions()


__all__ = ["default_signals_actions"]
