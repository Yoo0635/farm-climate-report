"""Generate simple Plan B recommendations."""

from __future__ import annotations

from src.lib.models import Signal


def generate_plan_b(signals: list[Signal]) -> str:
    if not signals:
        return "추가 대비책 없음"
    code = signals[0].code.upper()
    if code == "HEATWAVE":
        return "환풍기, 냉풍 장비 준비하고 물 공급 여유 확인"
    if code == "RAIN_MULTI":
        return "비 침투 시 비닐 덮개 보강, 양수기 비상 준비"
    if code == "STRONG_WIND":
        return "약한 가지는 지주로 보강하고, 느슨한 부자재 수거"
    if code == "LOW_TEMP":
        return "추가 보온재 확보 후 야간에 덮을 준비"
    return "현장 점검 강화 및 추가 인력 지원 요청"


__all__ = ["generate_plan_b"]
