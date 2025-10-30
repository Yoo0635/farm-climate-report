"""Scenario-based action mapping for demo coverage."""

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


def _rain_actions() -> List[Action]:
    return [
        Action(
            title="배수로 청소",
            timing_window="강우 전",
            trigger="3일 연속 강우 예보",
            icon=None,
            source_name="농촌진흥청",
            source_year=2021,
        ),
        Action(
            title="비닐하우스 통풍 점검",
            timing_window="강우 중",
            trigger="습도 90% 이상",
            icon=None,
            source_name="농업기술원",
            source_year=2023,
        ),
        Action(
            title="비 그친 뒤 병해 확인",
            timing_window="강우 종료 1일 내",
            trigger="잎 표면 수분",
            icon=None,
            source_name="농업과학원",
            source_year=2022,
        ),
    ]


def _wind_actions() -> List[Action]:
    return [
        Action(
            title="지주와 끈 재조임",
            timing_window="강풍 전",
            trigger="풍속 14m/s 예보",
            icon=None,
            source_name="기상청",
            source_year=2022,
        ),
        Action(
            title="시설물 출입문 고정",
            timing_window="강풍 발생 시",
            trigger="돌풍 경보",
            icon=None,
            source_name="농업기상센터",
            source_year=2023,
        ),
        Action(
            title="낙과·손상 과실 제거",
            timing_window="강풍 종료 1일 내",
            trigger="가지 손상",
            icon=None,
            source_name="농촌진흥청",
            source_year=2024,
        ),
    ]


def _lowtemp_actions() -> List[Action]:
    return [
        Action(
            title="보온커튼 조기 가동",
            timing_window="밤 10시 이전",
            trigger="최저기온 5°C 이하",
            icon=None,
            source_name="농업기술센터",
            source_year=2023,
        ),
        Action(
            title="관수 중단 후 배수",
            timing_window="냉해 예보 12시간 전",
            trigger="토양 수분 과다",
            icon=None,
            source_name="농진청",
            source_year=2021,
        ),
        Action(
            title="아침 햇빛 전 덮개 개방",
            timing_window="냉해 후 1일",
            trigger="온도 회복",
            icon=None,
            source_name="경기도 농업기술원",
            source_year=2022,
        ),
    ]


def map_scenario_to_actions(scenario: str) -> Tuple[List[Signal], List[Action]]:
    key = (scenario or "GENERAL").upper()
    if key == "HEATWAVE":
        return [
            Signal(type="climate", code="HEATWAVE", severity="경보")
        ], _heatwave_actions()
    if key in {"RAIN", "RAIN_MULTI", "RAINY"}:
        return [
            Signal(type="climate", code="RAIN_MULTI", severity="주의")
        ], _rain_actions()
    if key in {"WIND", "STRONG_WIND"}:
        return [
            Signal(type="climate", code="STRONG_WIND", severity="경보")
        ], _wind_actions()
    if key in {"LOW_TEMP", "LOWTEMP", "LOW-TEMP"}:
        return [
            Signal(type="climate", code="LOW_TEMP", severity="주의")
        ], _lowtemp_actions()
    # Default: provide generic placeholders
    return [Signal(type="climate", code=key, severity="일반")], _heatwave_actions()
