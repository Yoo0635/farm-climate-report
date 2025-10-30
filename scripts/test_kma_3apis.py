#!/usr/bin/env python3
"""Test KMA 3종 API (중기육상 + 중기기온 + 단기예보)"""

import asyncio
import json
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.aggregation.fetchers import KmaFetcher
from src.services.aggregation.models import AggregateProfile, ResolvedProfile
from src.services.aggregation.resolver import ProfileResolver


async def main():
    print("="*60)
    print("KMA 3종 API 테스트 (중기육상 + 중기기온 + 단기예보)")
    print("="*60)
    
    # Profile 설정
    profile = AggregateProfile(
        region="andong-si",
        crop="apple",
        stage="growing"
    )
    
    resolver = ProfileResolver()
    resolved = resolver.resolve(profile)
    
    print(f"\n지역 정보:")
    print(f"  - 지역: {profile.region}")
    print(f"  - 작물: {profile.crop}")
    print(f"  - 위경도: {resolved.lat}, {resolved.lon}")
    print(f"  - KMA 광역코드: {resolved.kma_area_code}")
    print(f"  - KMA 격자: nx={resolved.kma_grid['nx']}, ny={resolved.kma_grid['ny']}")
    
    # KMA Fetcher 실행
    fetcher = KmaFetcher()
    result = await fetcher.fetch(resolved)
    
    if not result:
        print("\n❌ KMA API 호출 실패")
        return 1
    
    print(f"\n✅ KMA API 호출 성공")
    print(f"  - 발표시각: {result.get('issued_at')}")
    print(f"  - Provenance: {result.get('provenance')}")
    
    # Daily 데이터
    daily = result.get("daily", [])
    print(f"\n[Daily 데이터] - {len(daily)}일")
    for entry in daily[:5]:  # 처음 5일만
        date = entry.get("date")
        tmin = entry.get("tmin_c")
        tmax = entry.get("tmax_c")
        summary = entry.get("summary")
        precip_prob = entry.get("precip_probability_pct")
        
        print(f"  {date}:")
        if tmin is not None or tmax is not None:
            print(f"    기온: {tmin}°C ~ {tmax}°C")
        if summary:
            print(f"    날씨: {summary}")
        if precip_prob is not None:
            print(f"    강수확률: {precip_prob}%")
    
    # Hourly 데이터
    hourly = result.get("hourly", [])
    print(f"\n[Hourly 데이터] - {len(hourly)}시간")
    for entry in hourly[:5]:  # 처음 5시간만
        ts = entry.get("ts")
        temp = entry.get("t_c")
        rh = entry.get("rh_pct")
        precip = entry.get("precip_mm")
        wind = entry.get("wind_ms")
        sky = entry.get("sky")
        pty = entry.get("pty")
        
        print(f"  {ts}:")
        if temp is not None:
            print(f"    기온: {temp}°C")
        if rh is not None:
            print(f"    습도: {rh}%")
        if wind is not None:
            print(f"    풍속: {wind}m/s")
        if sky:
            sky_text = {"1": "맑음", "3": "구름많음", "4": "흐림"}.get(sky, sky)
            print(f"    하늘: {sky_text}")
        if pty and pty != "0":
            pty_text = {"1": "비", "2": "비/눈", "3": "눈", "4": "소나기"}.get(pty, pty)
            print(f"    강수형태: {pty_text}")
    
    # 전체 JSON
    print(f"\n{'='*60}")
    print("전체 응답 (첫 3000자)")
    print(f"{'='*60}")
    print(json.dumps(result, indent=2, ensure_ascii=False)[:3000])
    
    await fetcher.aclose()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
