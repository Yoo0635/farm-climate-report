# Weather Insights Customization

## Overview
Enhanced `compute_weather_insights()` function in `src/services/aggregation/soft_hints.py` to support crop-specific weather thresholds while maintaining focus on weather pattern detection (not agricultural logic).

## Design Principle
**Backend responsibility:** Detect weather patterns using crop-specific thresholds  
**LLM responsibility:** Interpret agricultural implications via RAG + deep search

## Crop-Specific Parameters

### 1. Workable Windows (`_find_workable_windows`)
작업 가능 시간대 추출 - 비 없고, 바람 약하고, 적정 온도

| Crop | Max Wind (m/s) | Min Temp (°C) | Max Temp (°C) |
|------|----------------|---------------|---------------|
| apple | 7.0 | 5 | 30 |
| strawberry | 5.0 | 10 | 28 |
| default | 7.0 | 5 | 35 |

**Purpose:** Identify safe spraying/pruning/harvesting time slots based on wind tolerance

### 2. Disease Risk Conditions (`_detect_disease_conditions`)
병해충 발생 위험 기상 조건 탐지

| Crop | Humidity Threshold (%) | Temp Range (°C) | Target Disease |
|------|------------------------|-----------------|----------------|
| apple | 90 | 15-25 | 갈색무늬병/탄저병 |
| strawberry | 85 | 18-25 | 흰가루병 |
| default | 90 | 15-25 | 일반 병해충 |

**Purpose:** Detect weather conditions favorable for disease (high humidity + specific temp)  
**NOT doing:** Disease diagnosis or treatment recommendations (LLM's job)

### 3. Crop Stress Indicators (`_assess_crop_stress`)
작물 스트레스 지표 계산 (기상 기반)

| Crop | Heat Threshold (°C) | Cold Threshold (°C) | Wind Threshold (m/s) |
|------|---------------------|---------------------|----------------------|
| apple | 32 | -2 | 15 |
| strawberry | 30 | 0 | 12 |
| default | 32 | 0 | 15 |

**Purpose:** Flag extreme weather events that could cause physiological stress  
**NOT doing:** Crop damage assessment or recovery recommendations (LLM's job)

### 4. Daily Suitability (`_calculate_daily_suitability`)
일별 농작업 적합도 계산 (0~100점)

| Crop | Max Wind (m/s) | Min Temp (°C) | Max Temp (°C) | Max Precip (mm) |
|------|----------------|---------------|---------------|-----------------|
| apple | 7 | 5 | 30 | 5 |
| strawberry | 5 | 8 | 28 | 3 |
| default | 7 | 5 | 30 | 5 |

**Scoring Logic:**
- Start with 100 points
- Deduct for: excessive rain, strong wind, extreme temps, insufficient workable hours
- Result: 0-100 score + grade (매우 적합/적합/보통/부적합/매우 부적합)

**Purpose:** Quantify general work suitability based on weather comfort  
**NOT doing:** Specific task recommendations (LLM decides based on crop stage + score)

## Function Signatures

```python
def compute_weather_insights(
    daily: list[ClimateDaily],
    hourly: list[ClimateHourly],
    warnings: list[WeatherWarning],
    crop: str = "apple",
    stage: str | None = None,
) -> dict[str, Any]:
    """LLM이 활용하기 쉬운 농업 중심 기상 인사이트 생성 (작물/생육단계 맞춤형)"""
```

Helper functions:
- `_find_workable_windows(hourly, crop, stage)` - stage parameter reserved for future use
- `_detect_disease_conditions(hourly, daily, crop)` - uses crop-specific humidity/temp thresholds
- `_assess_crop_stress(hourly, daily, crop)` - uses crop-specific extreme weather thresholds
- `_calculate_daily_suitability(daily, hourly, crop)` - uses crop-specific work comfort thresholds

## Example Usage

```python
from src.services.aggregation.soft_hints import compute_weather_insights

insights = compute_weather_insights(
    daily=daily_forecasts,
    hourly=hourly_forecasts,
    warnings=weather_warnings,
    crop="apple",
    stage="flowering"  # Optional: reserved for future fine-tuning
)

# LLM receives structured insights:
# - workable_windows: [{date, workable_hours, time_slots}]
# - disease_risk_conditions: [{date, risk_level, factors, recommendation}]
# - crop_stress_indicators: {heat_stress, cold_stress, water_stress, wind_damage}
# - weather_events: [{type, subtype, date, impact}]
# - daily_suitability: [{date, score, grade, factors, workable_hours}]
# - trend_analysis: {short_term, medium_term, long_term}
```

## Integration with LLM Pipeline

**Current state:** Insights generation ready  
**Next step:** Update `src/services/briefs/generator.py` to:
1. Extract crop from user Profile
2. Call `compute_weather_insights(daily, hourly, warnings, crop=profile.crop)`
3. Include insights in LLM prompt instead of raw 240-hour data

## Testing

Run test script to preview output:
```powershell
python scripts/test_weather_insights.py
```

## Future Enhancements

1. **Stage-specific thresholds:** Use `stage` parameter to adjust thresholds
   - Example: "flowering" stage → lower wind tolerance (더 민감)
   - Example: "dormant" stage → wider temp tolerance

2. **More crops:** Add grape, rice, pepper to config dictionaries

3. **Regional calibration:** Adjust thresholds based on local climate norms

## Non-Goals (LLM's Domain)

❌ Fertilizer recommendations  
❌ Pest control chemical selection  
❌ Disease diagnosis  
❌ Harvest timing decisions  
❌ Crop-specific growth stage advice  

✅ Weather pattern detection with crop-appropriate sensitivity  
✅ Time window extraction for safe operations  
✅ Quantitative weather scoring for LLM reasoning  
