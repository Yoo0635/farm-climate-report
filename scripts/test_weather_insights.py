#!/usr/bin/env python3
"""기상 데이터 정제 결과 확인 - LLM에게 전달되는 인사이트 미리보기"""

import asyncio
import json
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.aggregation.aggregator import get_aggregation_service
from src.services.aggregation.models import AggregateRequest
from src.services.aggregation.soft_hints import compute_weather_insights


async def main():
    print("="*70)
    print("기상 데이터 정제 테스트: 원시 데이터 → LLM 친화적 인사이트")
    print("="*70)
    
    # 1. 데이터 수집
    print("\n[1단계] API에서 기상 데이터 수집 중...")
    service = get_aggregation_service()
    
    request = AggregateRequest(
        region="andong-si",
        crop="apple",
        stage="growing",
        demo=False  # 실제 API 호출
    )
    
    try:
        evidence = await service.aggregate(request)
    except Exception as e:
        print(f"❌ API 호출 실패: {e}")
        return 1
    
    print(f"✅ 수집 완료:")
    print(f"  - Daily 데이터: {len(evidence.climate.daily)}일")
    print(f"  - Hourly 데이터: {len(evidence.climate.hourly)}시간")
    print(f"  - 병해충 정보: {len(evidence.pest.bulletins)}건")
    
    # 2. 기존 soft_hints (간단한 정제)
    print(f"\n[2단계] 기존 Soft Hints:")
    print(f"  - 연속 강수일: {evidence.soft_hints.rain_run_max_days}일" if evidence.soft_hints else "  (없음)")
    print(f"  - 폭염 시간: {evidence.soft_hints.heat_hours_ge_33c}시간" if evidence.soft_hints and evidence.soft_hints.heat_hours_ge_33c else "  (없음)")
    print(f"  - 습한 밤: {evidence.soft_hints.wet_nights_count}일" if evidence.soft_hints and evidence.soft_hints.wet_nights_count else "  (없음)")
    
    # 3. 새로운 weather_insights (고도화된 정제)
    print(f"\n[3단계] 새로운 Weather Insights 생성 중...")
    insights = compute_weather_insights(
        daily=evidence.climate.daily,
        hourly=evidence.climate.hourly,
        warnings=evidence.climate.warnings,
    )
    
    print(f"\n{'='*70}")
    print("✨ LLM에게 전달될 측정값 (작물 구분 없이 모든 구간)")
    print(f"{'='*70}")
    
    # 주간 기상 조건
    print(f"\n📅 [주간 시간대별 기상 조건] (풍속/온도/강수 구간별)")
    daytime = insights.get("daytime_conditions", [])
    if daytime:
        for d in daytime[:3]:  # 처음 3일만
            print(f"  {d['date']}: 주간 {d['total_hours']}시간")
            print(f"    풍속: 0-3m/s({d['wind_bands']['calm_0_3']}h), "
                  f"3-5m/s({d['wind_bands']['light_3_5']}h), "
                  f"5-7m/s({d['wind_bands']['moderate_5_7']}h), "
                  f"7-10m/s({d['wind_bands']['strong_7_10']}h)")
            print(f"    온도: <5°C({d['temp_bands']['cold_below_5']}h), "
                  f"5-10°C({d['temp_bands']['cool_5_10']}h), "
                  f"10-20°C({d['temp_bands']['comfortable_10_20']}h), "
                  f"20-25°C({d['temp_bands']['warm_20_25']}h)")
            print(f"    강수: {d['rainy_hours']}시간")
            print(f"    평균: 기온 {d['avg_temp']}°C, 풍속 {d['avg_wind']}m/s")
    else:
        print("  (데이터 없음)")
    
    # 병해충 관련 조건
    print(f"\n🦠 [병해충 관련 기상 조건] (습도/온도 구간별 시간)")
    disease_conditions = insights.get("disease_favorable_conditions", [])
    if disease_conditions:
        for cond in disease_conditions[:3]:
            print(f"  {cond['date']}:")
            print(f"    습도 구간: 70-80%({cond['humidity_bands']['rh_70_80']}h), "
                  f"80-90%({cond['humidity_bands']['rh_80_90']}h), "
                  f"90%+({cond['humidity_bands']['rh_90_plus']}h)")
            print(f"    온도 구간: 15-20°C({cond['temp_bands']['t_15_20']}h), "
                  f"20-25°C({cond['temp_bands']['t_20_25']}h)")
            print(f"    잎 젖음: {cond['leaf_wet_hours']}시간")
            print(f"    야간 고습: {cond['night_pattern']['high_humid_hours']}시간 "
                  f"(평균 {cond['night_pattern']['avg_humidity']}%)")
    else:
        print("  (측정 데이터 없음)")
    
    # 기상 스트레스 측정
    print(f"\n🌡️  [기상 스트레스 측정] (극한 온도/강풍/무강수)")
    stress = insights.get("weather_stress_measurements", {})
    temp = stress.get("temperature", {})
    wind = stress.get("wind", {})
    precip = stress.get("precipitation", {})
    
    print(f"  온도:")
    print(f"    0°C 이하: {temp.get('hours_below_0', 0)}시간")
    print(f"    30-35°C: {temp.get('hours_30_35', 0)}시간")
    print(f"    35°C 이상: {temp.get('hours_above_35', 0)}시간")
    print(f"    최저/최고: {temp.get('min_temp')}°C / {temp.get('max_temp')}°C")
    
    print(f"  풍속:")
    print(f"    10-15 m/s: {wind.get('hours_10_15', 0)}시간")
    print(f"    15-20 m/s: {wind.get('hours_15_20', 0)}시간")
    print(f"    20+ m/s: {wind.get('hours_above_20', 0)}시간")
    print(f"    최대: {wind.get('max_wind')} m/s")
    
    print(f"  강수:")
    print(f"    무강수일: {precip.get('dry_days', 0)}일 (연속 {precip.get('consecutive_dry_days', 0)}일)")
    
    # 일사량 측정
    print(f"\n☀️  [일사량 측정] (광합성/증산작용, Open-Meteo)")
    solar = insights.get("solar_radiation_measurements", {})
    solar_daily = solar.get("daily", [])
    if solar_daily:
        for s in solar_daily[:3]:  # 처음 3일
            print(f"  {s['date']}:")
            print(f"    일조 시간: {s['sunshine_hours']}시간 (>120 W/m²)")
            print(f"    누적 일사량: {s['total_radiation_mj_m2']} MJ/m²")
            print(f"    평균/최대: {s['avg_radiation_wm2']} / {s['max_radiation_wm2']} W/m²")
            print(f"    일사 구간: 어두움({s['radiation_bands']['dark_0_50']}h), "
                  f"약광({s['radiation_bands']['dim_50_200']}h), "
                  f"보통({s['radiation_bands']['moderate_200_500']}h), "
                  f"강광({s['radiation_bands']['bright_500_800']}h)")
    else:
        print(f"  데이터 없음 - {solar.get('note', 'Open-Meteo 미수신')}")
    
    # 주요 기상 이벤트
    print(f"\n⚠️  [주요 기상 이벤트 타임라인]")
    events = insights.get("weather_events", [])
    if events:
        for event in events[:5]:  # 처음 5개만
            date_str = event.get("date") or event.get("start", "")[:10]
            print(f"  {date_str}: {event['type']} - {event['subtype']}")
            if event.get("amount_mm"):
                print(f"    강수량: {event['amount_mm']}mm")
            if event.get("max_temp"):
                print(f"    최고기온: {event['max_temp']}°C")
    else:
        print("  (특이 기상 이벤트 없음)")
    
    # 일별 조건 요약
    print(f"\n✅ [일별 기상 조건 요약] (주간 강수/풍속/온도)")
    daily_conds = insights.get("daily_conditions", [])
    for d in daily_conds:
        print(f"  {d['date']}: 주간 {d['daytime_hours']}시간")
        print(f"    강수: {d['precipitation']['total_mm']}mm ({d['precipitation']['rainy_hours']}시간)")
        print(f"    풍속: 평균 {d['wind']['avg_speed']} m/s "
              f"(약풍 {d['wind']['hours_by_strength']['calm']}h, "
              f"강풍 {d['wind']['hours_by_strength']['very_strong']}h)")
        print(f"    온도: {d['temperature']['min']}-{d['temperature']['max']}°C "
              f"(쾌적 {d['temperature']['hours_by_range']['comfortable']}h)")
    
    # 기상 트렌드
    print(f"\n📊 [기상 트렌드 분석]")
    trends = insights.get("trend_analysis", {})
    
    if trends.get("next_3days"):
        t3 = trends["next_3days"]
        print(f"  향후 3일: 평균 {t3.get('avg_temp')}°C, 강수 {t3.get('total_precip')}mm")
    
    if trends.get("next_7days"):
        t7 = trends["next_7days"]
        print(f"  향후 7일: 평균 {t7.get('avg_temp')}°C, 비오는 날 {t7.get('rainy_days')}일")
    
    if trends.get("temperature_trend"):
        print(f"  기온 추세: {trends['temperature_trend']}")
    
    # 전체 JSON 출력
    print(f"\n{'='*70}")
    print("전체 인사이트 JSON (LLM 프롬프트에 포함될 내용)")
    print(f"{'='*70}")
    print(json.dumps(insights, indent=2, ensure_ascii=False, default=str))
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
