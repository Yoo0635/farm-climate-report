"""작물별 맞춤 기상 조건 및 임계값 정의"""

from __future__ import annotations

from typing import Any


# 작물별 기상 작업 조건
CROP_WORK_CONDITIONS = {
    "apple": {
        "name": "사과",
        "min_temp": 5,      # 최저 작업 온도
        "max_temp": 35,     # 최고 작업 온도
        "max_wind": 7.0,    # 방제 작업 최대 풍속 (m/s)
        "work_hours": (6, 18),  # 작업 가능 시간
        "optimal_temp_range": (15, 25),  # 최적 작업 온도
    },
    "rice": {
        "name": "논벼",
        "min_temp": 10,
        "max_temp": 38,
        "max_wind": 10.0,
        "work_hours": (7, 19),
        "optimal_temp_range": (20, 30),
    },
    "grape": {
        "name": "포도",
        "min_temp": 8,
        "max_temp": 35,
        "max_wind": 6.0,  # 포도는 더 민감
        "work_hours": (7, 18),
        "optimal_temp_range": (18, 28),
    },
    "pepper": {
        "name": "고추",
        "min_temp": 12,
        "max_temp": 35,
        "max_wind": 8.0,
        "work_hours": (6, 18),
        "optimal_temp_range": (20, 30),
    },
}


# 작물별 병해충 발생 조건
CROP_DISEASE_CONDITIONS = {
    "apple": {
        "갈색무늬병": {
            "temp_range": (15, 25),
            "min_humidity": 85,
            "wet_hours_threshold": 6,
            "risk_season": (5, 9),  # 5월~9월
        },
        "점무늬낙엽병": {
            "temp_range": (20, 30),
            "min_humidity": 90,
            "wet_hours_threshold": 4,
            "risk_season": (6, 9),
        },
        "탄저병": {
            "temp_range": (25, 30),
            "min_humidity": 95,
            "wet_hours_threshold": 8,
            "risk_season": (7, 9),
        },
    },
    "rice": {
        "도열병": {
            "temp_range": (20, 28),
            "min_humidity": 90,
            "wet_hours_threshold": 10,
            "risk_season": (6, 8),
        },
        "잎집무늬마름병": {
            "temp_range": (25, 32),
            "min_humidity": 85,
            "wet_hours_threshold": 6,
            "risk_season": (7, 9),
        },
    },
}


# 생육 단계별 중요 기상 요소
GROWTH_STAGE_PRIORITIES = {
    "apple": {
        "dormant": {  # 휴면기
            "critical_factors": ["저온", "동해"],
            "temp_threshold": {"min": -15, "max": 5},
            "monitoring": ["최저기온", "급격한 온도 변화"],
        },
        "flowering": {  # 개화기
            "critical_factors": ["서리", "강우", "수분"],
            "temp_threshold": {"min": 0, "max": 30},
            "monitoring": ["최저기온", "개화기 강우", "바람"],
        },
        "growing": {  # 생육기
            "critical_factors": ["병해충", "수분", "일사량"],
            "temp_threshold": {"min": 10, "max": 35},
            "monitoring": ["습도", "강우 패턴", "일조 시간"],
        },
        "harvest": {  # 수확기
            "critical_factors": ["강우", "태풍", "착색"],
            "temp_threshold": {"min": 5, "max": 30},
            "monitoring": ["강우 시기", "일교차", "바람"],
        },
    },
    "rice": {
        "transplanting": {  # 이앙기
            "critical_factors": ["저온", "수온"],
            "temp_threshold": {"min": 13, "max": 35},
            "monitoring": ["수온", "야간 기온"],
        },
        "tillering": {  # 분얼기
            "critical_factors": ["온도", "일조"],
            "temp_threshold": {"min": 15, "max": 35},
            "monitoring": ["평균 기온", "일조 시간"],
        },
        "heading": {  # 출수기
            "critical_factors": ["고온", "병해충"],
            "temp_threshold": {"min": 20, "max": 33},
            "monitoring": ["고온", "습도", "바람"],
        },
    },
}


# 작물별 스트레스 임계값
CROP_STRESS_THRESHOLDS = {
    "apple": {
        "heat_stress": 33,      # 고온 스트레스 시작 온도
        "cold_stress": 5,       # 저온 스트레스 시작 온도
        "frost_damage": -2,     # 동해 위험 온도
        "drought_days": 7,      # 관수 필요 무강수 일수
        "waterlogging_mm": 100, # 침수 위험 강수량 (3일 누적)
    },
    "rice": {
        "heat_stress": 35,
        "cold_stress": 13,
        "frost_damage": 0,
        "drought_days": 5,
        "waterlogging_mm": 150,
    },
    "grape": {
        "heat_stress": 35,
        "cold_stress": 8,
        "frost_damage": -1,
        "drought_days": 10,
        "waterlogging_mm": 80,
    },
}


def get_crop_config(crop: str, stage: str | None = None) -> dict[str, Any]:
    """작물과 생육 단계에 맞는 설정 반환"""
    config = {
        "work_conditions": CROP_WORK_CONDITIONS.get(crop, CROP_WORK_CONDITIONS["apple"]),
        "disease_conditions": CROP_DISEASE_CONDITIONS.get(crop, {}),
        "stress_thresholds": CROP_STRESS_THRESHOLDS.get(crop, CROP_STRESS_THRESHOLDS["apple"]),
    }
    
    if stage:
        stage_info = GROWTH_STAGE_PRIORITIES.get(crop, {}).get(stage)
        if stage_info:
            config["stage_priorities"] = stage_info
    
    return config


__all__ = [
    "CROP_WORK_CONDITIONS",
    "CROP_DISEASE_CONDITIONS",
    "GROWTH_STAGE_PRIORITIES",
    "CROP_STRESS_THRESHOLDS",
    "get_crop_config",
]
