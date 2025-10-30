#!/usr/bin/env python3
"""Test Open-Meteo API to see what data we get."""

import json
from urllib.request import urlopen
from urllib.parse import urlencode

def test_current_params():
    """현재 fetchers.py에서 사용하는 파라미터"""
    params = {
        "latitude": 36.568,
        "longitude": 128.729,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_gusts_10m,precipitation,shortwave_radiation",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max",
        "forecast_days": "10",
        "timezone": "Asia/Seoul",
    }
    
    url = f"https://api.open-meteo.com/v1/forecast?{urlencode(params)}"
    print(f"URL: {url}\n")
    
    with urlopen(url, timeout=20) as response:
        data = json.loads(response.read().decode('utf-8'))
    
    print("="*60)
    print("현재 fetchers.py 설정으로 가져오는 데이터")
    print("="*60)
    
    # Daily 정보
    print("\n[Daily 데이터]")
    daily = data.get("daily", {})
    print(f"- 날짜 수: {len(daily.get('time', []))}일")
    print(f"- 파라미터: {list(daily.keys())}")
    if daily.get("time"):
        print(f"\n첫째 날 예시 ({daily['time'][0]}):")
        for key, values in daily.items():
            if key != "time" and values:
                print(f"  {key}: {values[0]}")
    
    # Hourly 정보
    print("\n[Hourly 데이터]")
    hourly = data.get("hourly", {})
    print(f"- 시간 수: {len(hourly.get('time', []))}시간")
    print(f"- 파라미터: {list(hourly.keys())}")
    if hourly.get("time"):
        print(f"\n첫 시간 예시 ({hourly['time'][0]}):")
        for key, values in hourly.items():
            if key != "time" and values:
                print(f"  {key}: {values[0]}")
    
    # 메타데이터
    print("\n[메타 정보]")
    print(f"- 위도: {data.get('latitude')}")
    print(f"- 경도: {data.get('longitude')}")
    print(f"- 고도: {data.get('elevation')}m")
    print(f"- 시간대: {data.get('timezone')}")
    print(f"- 생성시각: {data.get('generationtime_ms')}ms")
    
    print("\n" + "="*60)
    print("전체 JSON (첫 3000자)")
    print("="*60)
    print(json.dumps(data, indent=2, ensure_ascii=False)[:3000])

if __name__ == "__main__":
    test_current_params()
