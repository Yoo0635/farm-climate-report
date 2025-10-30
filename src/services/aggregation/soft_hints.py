"""Deterministic helper calculations for optional soft hints.

Enhanced with agriculture-focused weather pattern detection for LLM context.
Now supports crop and growth-stage customization.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from src.services.aggregation.models import ClimateDaily, ClimateHourly, SoftHints, WeatherWarning
from src.services.aggregation.crop_configs import get_crop_config


def compute_soft_hints(
    daily: list[ClimateDaily],
    hourly: list[ClimateHourly],
    warnings: list[WeatherWarning],
) -> SoftHints:
    """기본 soft hints 계산 (기존 호환성 유지)"""
    return SoftHints(
        rain_run_max_days=_rain_run_max_days(daily),
        heat_hours_ge_33c=_count_hours(hourly, field="t_c", threshold=33.0),
        wind_hours_ge_10ms=_count_hours(hourly, field="wind_ms", threshold=10.0),
        wet_nights_count=_wet_nights(hourly),
        diurnal_range_max=_diurnal_range_max(daily),
        first_warning_type=warnings[0].type if warnings else None,
    )


def compute_weather_insights(
    daily: list[ClimateDaily],
    hourly: list[ClimateHourly],
    warnings: list[WeatherWarning],
) -> dict[str, Any]:
    """LLM이 활용하기 쉬운 기상 인사이트 생성 (측정값만, 판단/작물별 임계값 제외)
    
    백엔드: 기상 데이터를 구간별로 측정
    LLM: RAG 지식 + 측정값 → 작물별 판단
    """
    
    return {
        # 1. 주간 시간대별 기상 조건 (풍속/온도/강수 구간별)
        "daytime_conditions": _find_workable_windows(hourly),
        
        # 2. 병해충 관련 기상 조건 (습도/온도 구간별 시간)
        "disease_favorable_conditions": _detect_disease_conditions(hourly, daily),
        
        # 3. 기상 스트레스 요인 측정 (극한 온도/강풍/무강수)
        "weather_stress_measurements": _assess_crop_stress(hourly, daily),
        
        # 4. 주요 기상 이벤트 타임라인
        "weather_events": _extract_weather_events(daily, hourly, warnings),
        
        # 5. 일별 기상 조건 요약
        "daily_conditions": _calculate_daily_suitability(daily, hourly),
        
        # 6. 3일/7일/10일 기상 트렌드
        "trend_analysis": _analyze_weather_trends(daily),
    }


def _rain_run_max_days(daily: list[ClimateDaily]) -> int | None:
    run = 0
    best = 0
    for entry in daily:
        if entry.precip_mm is not None and entry.precip_mm > 0:
            run += 1
            best = max(best, run)
        else:
            run = 0
    return best or None


def _count_hours(hourly: list[ClimateHourly], field: str, threshold: float) -> int | None:
    total = 0
    for entry in hourly:
        value = getattr(entry, field, None)
        if value is not None and value >= threshold:
            total += 1
    return total or None


def _wet_nights(hourly: list[ClimateHourly]) -> int | None:
    counts: dict[str, int] = defaultdict(int)
    for entry in hourly:
        ts = entry.ts
        if entry.rh_pct is None or entry.rh_pct < 90:
            continue
        if 21 <= ts.hour <= 23:
            key_date = ts.date().isoformat()
        elif 0 <= ts.hour <= 5:
            key_date = (ts - timedelta(days=1)).date().isoformat()
        else:
            continue
        counts[key_date] += 1

    qualifying = sum(1 for freq in counts.values() if freq >= 3)
    return qualifying or None


def _diurnal_range_max(daily: list[ClimateDaily]) -> float | None:
    ranges: list[float] = []
    for entry in daily:
        if entry.tmax_c is None or entry.tmin_c is None:
            continue
        ranges.append(entry.tmax_c - entry.tmin_c)
    if not ranges:
        return None
    return max(ranges)


# ============================================================================
# LLM 친화적 기상 인사이트 함수들
# ============================================================================

def _find_workable_windows(hourly: list[ClimateHourly]) -> list[dict[str, Any]]:
    """시간대별 기상 조건 측정 (모든 구간)
    
    작업 적합성은 LLM이 판단하도록 측정값만 제공:
    - 시간별 강수량, 풍속, 온도, 습도
    - 주간(06-18시) 시간대만 추출
    """
    windows = []
    
    # 주간(06-18시) 모든 시간대 수집 (필터링 없이)
    for entry in hourly[:72]:  # 3일간만
        hour = entry.ts.hour
        if 6 <= hour <= 18:  # 주간 작업 시간
            windows.append({
                "datetime": entry.ts.isoformat(),
                "date": entry.ts.date().isoformat(),
                "hour": hour,
                "temp_c": entry.t_c,
                "wind_ms": entry.wind_ms,
                "rh_pct": entry.rh_pct,
                "precip_mm": entry.precip_mm,
            })
    
    # 날짜별로 그룹화
    daily_windows: dict[str, list[dict]] = defaultdict(list)
    for w in windows:
        daily_windows[w["date"]].append(w)
    
    result = []
    for day, hours in sorted(daily_windows.items()):
        # 풍속 구간별 시간
        wind_bands = {
            "calm_0_3": len([h for h in hours if h.get("wind_ms") and h["wind_ms"] < 3]),
            "light_3_5": len([h for h in hours if h.get("wind_ms") and 3 <= h["wind_ms"] < 5]),
            "moderate_5_7": len([h for h in hours if h.get("wind_ms") and 5 <= h["wind_ms"] < 7]),
            "strong_7_10": len([h for h in hours if h.get("wind_ms") and 7 <= h["wind_ms"] < 10]),
            "very_strong_10_plus": len([h for h in hours if h.get("wind_ms") and h["wind_ms"] >= 10]),
        }
        
        # 온도 구간별 시간
        temp_bands = {
            "cold_below_5": len([h for h in hours if h.get("temp_c") and h["temp_c"] < 5]),
            "cool_5_10": len([h for h in hours if h.get("temp_c") and 5 <= h["temp_c"] < 10]),
            "comfortable_10_20": len([h for h in hours if h.get("temp_c") and 10 <= h["temp_c"] < 20]),
            "warm_20_25": len([h for h in hours if h.get("temp_c") and 20 <= h["temp_c"] < 25]),
            "hot_25_30": len([h for h in hours if h.get("temp_c") and 25 <= h["temp_c"] < 30]),
            "very_hot_30_plus": len([h for h in hours if h.get("temp_c") and h["temp_c"] >= 30]),
        }
        
        # 강수 시간
        rainy_hours = len([h for h in hours if h.get("precip_mm") and h["precip_mm"] > 0])
        
        result.append({
            "date": day,
            "total_hours": len(hours),
            "wind_bands": wind_bands,
            "temp_bands": temp_bands,
            "rainy_hours": rainy_hours,
            "avg_temp": round(sum(h.get("temp_c", 0) or 0 for h in hours) / len(hours), 1) if hours else None,
            "avg_wind": round(sum(h.get("wind_ms", 0) or 0 for h in hours) / len(hours), 1) if hours else None,
        })
    
    return result


def _detect_disease_conditions(hourly: list[ClimateHourly], daily: list[ClimateDaily]) -> list[dict[str, Any]]:
    """병해충 관련 기상 조건 측정 (판단 없이 팩트만)
    
    측정 항목:
    - 고습도 시간 (습도별 구간: 70-80%, 80-90%, 90%+)
    - 온도 구간별 시간 (5도 단위)
    - 잎 젖음 시간 (강수 + 95% 이상 습도)
    - 야간 습도 패턴
    """
    conditions: list[dict[str, Any]] = []
    
    # 일별로 그룹화
    hourly_by_date: dict[str, list[ClimateHourly]] = defaultdict(list)
    for entry in hourly[:72]:
        hourly_by_date[entry.ts.date().isoformat()].append(entry)
    
    for day_str, hours in hourly_by_date.items():
        # 습도 구간별 시간 측정
        humidity_bands = {
            "rh_70_80": len([h for h in hours if h.rh_pct and 70 <= h.rh_pct < 80]),
            "rh_80_90": len([h for h in hours if h.rh_pct and 80 <= h.rh_pct < 90]),
            "rh_90_plus": len([h for h in hours if h.rh_pct and h.rh_pct >= 90]),
        }
        
        # 온도 구간별 시간 측정 (5도 단위)
        temp_bands = {
            "t_below_5": len([h for h in hours if h.t_c and h.t_c < 5]),
            "t_5_10": len([h for h in hours if h.t_c and 5 <= h.t_c < 10]),
            "t_10_15": len([h for h in hours if h.t_c and 10 <= h.t_c < 15]),
            "t_15_20": len([h for h in hours if h.t_c and 15 <= h.t_c < 20]),
            "t_20_25": len([h for h in hours if h.t_c and 20 <= h.t_c < 25]),
            "t_25_30": len([h for h in hours if h.t_c and 25 <= h.t_c < 30]),
            "t_30_plus": len([h for h in hours if h.t_c and h.t_c >= 30]),
        }
        
        # 잎 젖음 조건 (강수 or 매우 높은 습도)
        leaf_wet_hours = len([
            h for h in hours
            if (h.precip_mm and h.precip_mm > 0) or (h.rh_pct and h.rh_pct >= 95)
        ])
        
        # 야간(21-05시) 습도 패턴
        night_hours = [h for h in hours if 21 <= h.ts.hour <= 23 or 0 <= h.ts.hour <= 5]
        night_humid_hours = len([h for h in night_hours if h.rh_pct and h.rh_pct >= 85])
        night_avg_rh = sum(h.rh_pct for h in night_hours if h.rh_pct) / len(night_hours) if night_hours else None
        
        conditions.append({
            "date": day_str,
            "humidity_bands": humidity_bands,
            "temp_bands": temp_bands,
            "leaf_wet_hours": leaf_wet_hours,
            "night_pattern": {
                "high_humid_hours": night_humid_hours,
                "avg_humidity": round(night_avg_rh, 1) if night_avg_rh else None,
            },
        })
    
    return conditions


def _assess_crop_stress(hourly: list[ClimateHourly], daily: list[ClimateDaily]) -> dict[str, Any]:
    """기상 스트레스 요인 측정 (판단 없이 측정값만)
    
    측정 항목:
    - 온도 구간별 시간 (극한 온도 포함)
    - 강풍 구간별 시간
    - 무강수 연속일
    """
    measurements = {
        "temperature": {
            "hours_below_0": 0,
            "hours_0_5": 0,
            "hours_5_10": 0,
            "hours_30_35": 0,
            "hours_above_35": 0,
            "min_temp": None,
            "max_temp": None,
            "extreme_dates": [],
        },
        "wind": {
            "hours_10_15": 0,
            "hours_15_20": 0,
            "hours_above_20": 0,
            "max_wind": None,
            "strong_wind_dates": [],
        },
        "precipitation": {
            "dry_days": 0,
            "consecutive_dry_days": 0,
            "dry_dates": [],
        },
    }
    
    # 온도 측정 (시간별)
    for entry in hourly[:72]:
        if entry.t_c is None:
            continue
            
        # 온도 구간별 카운트
        if entry.t_c < 0:
            measurements["temperature"]["hours_below_0"] += 1
        elif 0 <= entry.t_c < 5:
            measurements["temperature"]["hours_0_5"] += 1
        elif 5 <= entry.t_c < 10:
            measurements["temperature"]["hours_5_10"] += 1
        elif 30 <= entry.t_c < 35:
            measurements["temperature"]["hours_30_35"] += 1
        elif entry.t_c >= 35:
            measurements["temperature"]["hours_above_35"] += 1
        
        # 최저/최고 온도
        if measurements["temperature"]["min_temp"] is None or entry.t_c < measurements["temperature"]["min_temp"]:
            measurements["temperature"]["min_temp"] = entry.t_c
        if measurements["temperature"]["max_temp"] is None or entry.t_c > measurements["temperature"]["max_temp"]:
            measurements["temperature"]["max_temp"] = entry.t_c
        
        # 극한 온도 날짜 기록
        if entry.t_c < 0 or entry.t_c >= 33:
            date_str = entry.ts.date().isoformat()
            if date_str not in measurements["temperature"]["extreme_dates"]:
                measurements["temperature"]["extreme_dates"].append(date_str)
    
    # 강풍 측정 (시간별)
    for entry in hourly[:72]:
        wind = entry.wind_ms or entry.gust_ms
        if wind is None:
            continue
            
        # 풍속 구간별 카운트
        if 10 <= wind < 15:
            measurements["wind"]["hours_10_15"] += 1
        elif 15 <= wind < 20:
            measurements["wind"]["hours_15_20"] += 1
        elif wind >= 20:
            measurements["wind"]["hours_above_20"] += 1
        
        # 최대 풍속
        if measurements["wind"]["max_wind"] is None or wind > measurements["wind"]["max_wind"]:
            measurements["wind"]["max_wind"] = wind
        
        # 강풍 날짜 기록 (10m/s 이상)
        if wind >= 10:
            date_str = entry.ts.date().isoformat()
            if date_str not in measurements["wind"]["strong_wind_dates"]:
                measurements["wind"]["strong_wind_dates"].append(date_str)
    
    # 무강수 측정 (일별)
    dry_run = 0
    max_dry_run = 0
    for entry in daily[:7]:
        if entry.precip_mm is None or entry.precip_mm < 1.0:
            dry_run += 1
            max_dry_run = max(max_dry_run, dry_run)
            measurements["precipitation"]["dry_dates"].append(entry.date)
        else:
            dry_run = 0
    
    measurements["precipitation"]["dry_days"] = len(measurements["precipitation"]["dry_dates"])
    measurements["precipitation"]["consecutive_dry_days"] = max_dry_run
    
    return measurements


def _extract_weather_events(
    daily: list[ClimateDaily], 
    hourly: list[ClimateHourly], 
    warnings: list[WeatherWarning]
) -> list[dict[str, Any]]:
    """주요 기상 이벤트 타임라인 생성"""
    events: list[dict[str, Any]] = []
    
    # 특보
    for warning in warnings:
        events.append({
            "type": "기상특보",
            "subtype": warning.type,
            "severity": warning.level,
            "start": warning.from_.isoformat(),
            "end": warning.to.isoformat(),
            "impact": "높음",
        })
    
    # 강수 이벤트
    for entry in daily[:7]:
        if entry.precip_mm and entry.precip_mm > 10:
            events.append({
                "type": "강수",
                "subtype": "많은 비" if entry.precip_mm > 30 else "비",
                "date": entry.date,
                "amount_mm": entry.precip_mm,
                "impact": "높음" if entry.precip_mm > 30 else "보통",
            })
    
    # 극한 기온
    for entry in daily[:7]:
        if entry.tmax_c and entry.tmax_c >= 33:
            events.append({
                "type": "고온",
                "subtype": "폭염",
                "date": entry.date,
                "max_temp": entry.tmax_c,
                "impact": "높음",
            })
        if entry.tmin_c and entry.tmin_c <= 0:
            events.append({
                "type": "저온",
                "subtype": "영하",
                "date": entry.date,
                "min_temp": entry.tmin_c,
                "impact": "높음",
            })
    
    # 시간순 정렬
    events.sort(key=lambda e: e.get("date") or e.get("start", ""))
    
    return events


def _calculate_daily_suitability(daily: list[ClimateDaily], hourly: list[ClimateHourly]) -> list[dict[str, Any]]:
    """일별 기상 조건 요약 (판단 없이 측정값만)
    
    측정 항목:
    - 주간(06-18시) 강수 시간, 강풍 시간, 적정 온도 시간
    - 일 최고/최저 온도, 총 강수량, 평균 풍속
    """
    daily_summaries: list[dict[str, Any]] = []
    
    # 시간별 데이터를 날짜별로 그룹화
    hourly_by_date: dict[str, list[ClimateHourly]] = defaultdict(list)
    for entry in hourly[:72]:
        hourly_by_date[entry.ts.date().isoformat()].append(entry)
    
    for day_entry in daily[:3]:  # 3일간만
        day_str = day_entry.date if isinstance(day_entry.date, str) else day_entry.date.isoformat()
        day_hours = hourly_by_date.get(day_str, [])
        
        # 주간(06-18시) 시간대 필터링
        daytime_hours = [h for h in day_hours if 6 <= h.ts.hour <= 18]
        
        # 강수 시간 측정
        rainy_hours = len([h for h in daytime_hours if h.precip_mm and h.precip_mm > 0])
        
        # 풍속 구간별 시간 측정
        wind_bands = {
            "calm": len([h for h in daytime_hours if h.wind_ms and h.wind_ms < 3]),
            "moderate": len([h for h in daytime_hours if h.wind_ms and 3 <= h.wind_ms < 7]),
            "strong": len([h for h in daytime_hours if h.wind_ms and 7 <= h.wind_ms < 10]),
            "very_strong": len([h for h in daytime_hours if h.wind_ms and h.wind_ms >= 10]),
        }
        
        # 온도 구간별 시간 측정
        temp_bands = {
            "cold": len([h for h in daytime_hours if h.t_c and h.t_c < 10]),
            "comfortable": len([h for h in daytime_hours if h.t_c and 10 <= h.t_c < 25]),
            "warm": len([h for h in daytime_hours if h.t_c and 25 <= h.t_c < 30]),
            "hot": len([h for h in daytime_hours if h.t_c and h.t_c >= 30]),
        }
        
        daily_summaries.append({
            "date": day_str,
            "daytime_hours": len(daytime_hours),
            "precipitation": {
                "total_mm": day_entry.precip_mm,
                "rainy_hours": rainy_hours,
            },
            "wind": {
                "avg_speed": day_entry.wind_ms,
                "hours_by_strength": wind_bands,
            },
            "temperature": {
                "min": day_entry.tmin_c,
                "max": day_entry.tmax_c,
                "hours_by_range": temp_bands,
            },
        })
    
    return daily_summaries


def _analyze_weather_trends(daily: list[ClimateDaily]) -> dict[str, Any]:
    """3일/7일/10일 기상 트렌드 분석"""
    if not daily:
        return {}
    
    def _get_period_stats(period_days: list[ClimateDaily]) -> dict[str, Any]:
        temps = [d.tmax_c for d in period_days if d.tmax_c is not None]
        precips = [d.precip_mm for d in period_days if d.precip_mm is not None]
        
        return {
            "avg_temp": round(sum(temps) / len(temps), 1) if temps else None,
            "max_temp": max(temps) if temps else None,
            "min_temp": min([d.tmin_c for d in period_days if d.tmin_c is not None], default=None),
            "total_precip": round(sum(precips), 1) if precips else 0,
            "rainy_days": len([p for p in precips if p > 1.0]),
        }
    
    trends = {}
    
    if len(daily) >= 3:
        trends["next_3days"] = _get_period_stats(daily[:3])
    if len(daily) >= 7:
        trends["next_7days"] = _get_period_stats(daily[:7])
    if len(daily) >= 10:
        trends["next_10days"] = _get_period_stats(daily[:10])
    
    # 트렌드 방향
    if len(daily) >= 3:
        temps_trend = []
        for i in range(min(3, len(daily))):
            if daily[i].tmax_c:
                temps_trend.append(daily[i].tmax_c)
        
        if len(temps_trend) >= 2:
            if temps_trend[-1] > temps_trend[0] + 3:
                trends["temperature_trend"] = "상승"
            elif temps_trend[-1] < temps_trend[0] - 3:
                trends["temperature_trend"] = "하강"
            else:
                trends["temperature_trend"] = "안정"
    
    return trends


__all__ = ["compute_soft_hints", "compute_weather_insights"]
