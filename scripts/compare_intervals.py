#!/usr/bin/env python3
"""KMA와 Open-Meteo 데이터 주기 비교"""

import asyncio
import sys
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.aggregation.fetchers import OpenMeteoFetcher, KmaFetcher
from src.services.aggregation.resolver import ProfileResolver
from src.services.aggregation.models import AggregateRequest, AggregateProfile


async def check_intervals():
    profile = AggregateProfile(region='andong-si', crop='apple', stage='growing')
    resolver = ProfileResolver()
    resolved = resolver.resolve(profile)
    
    print("="*70)
    print("데이터 주기 비교: KMA vs Open-Meteo")
    print("="*70)
    
    # Open-Meteo
    print("\n[Open-Meteo]")
    om = OpenMeteoFetcher()
    om_data = await om.fetch(resolved)
    
    if om_data:
        om_hourly = om_data.get('hourly', [])
        om_daily = om_data.get('daily', [])
        
        print(f"Hourly: {len(om_hourly)}개")
        if len(om_hourly) >= 5:
            print("  첫 5개 타임스탬프:")
            for h in om_hourly[:5]:
                print(f"    {h['ts']}")
        
        print(f"\nDaily: {len(om_daily)}개")
        if len(om_daily) >= 3:
            print("  첫 3개 날짜:")
            for d in om_daily[:3]:
                print(f"    {d['date']}")
    else:
        print("  데이터 없음")
    
    # KMA
    print("\n[KMA (Mid + Short 통합)]")
    kma = KmaFetcher()
    kma_data = await kma.fetch(resolved)
    
    if kma_data:
        kma_hourly = kma_data.get('hourly', [])
        kma_daily = kma_data.get('daily', [])
        
        print(f"Hourly: {len(kma_hourly)}개")
        if len(kma_hourly) >= 5:
            print("  첫 5개 타임스탬프:")
            for h in kma_hourly[:5]:
                print(f"    {h['ts']}")
        
        print(f"\nDaily: {len(kma_daily)}개")
        if len(kma_daily) >= 3:
            print("  첫 3개 날짜:")
            for d in kma_daily[:3]:
                print(f"    {d['date']}")
    else:
        print("  데이터 없음")
    
    # 주기 분석
    print("\n" + "="*70)
    print("주기 분석")
    print("="*70)
    
    if om_data and om_data.get('hourly') and len(om_data['hourly']) >= 2:
        from datetime import datetime
        ts1 = datetime.fromisoformat(om_data['hourly'][0]['ts'])
        ts2 = datetime.fromisoformat(om_data['hourly'][1]['ts'])
        interval = (ts2 - ts1).total_seconds() / 3600
        print(f"Open-Meteo Hourly 간격: {interval}시간")
    
    if kma_data and kma_data.get('hourly') and len(kma_data['hourly']) >= 2:
        from datetime import datetime
        ts1 = datetime.fromisoformat(kma_data['hourly'][0]['ts'])
        ts2 = datetime.fromisoformat(kma_data['hourly'][1]['ts'])
        interval = (ts2 - ts1).total_seconds() / 3600
        print(f"KMA Hourly 간격: {interval}시간")
    
    print("\n결론:")
    print("- Open-Meteo: 1시간 간격")
    print("- KMA Short: 3시간 간격 (단기예보 403 에러로 미수신 가능)")
    print("⚠️  주기가 다르므로 merge 시 주의 필요!")


if __name__ == "__main__":
    asyncio.run(check_intervals())
