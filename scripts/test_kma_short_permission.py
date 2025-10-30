#!/usr/bin/env python3
"""KMA 단기예보 API 권한 테스트"""

import os
import httpx
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def test_short_permission():
    api_key = os.environ.get("KMA_API_KEY")
    if not api_key:
        print("❌ KMA_API_KEY 환경변수가 설정되지 않았습니다.")
        return
    
    print("="*70)
    print("KMA 단기예보 API 권한 테스트")
    print("="*70)
    print(f"API Key: {api_key[:20]}...")
    
    # 단기예보 URL
    endpoint = "https://apihub.kma.go.kr/api/typ02/openApi/VilageFcstInfoService_2.0/getVilageFcst"
    
    now = datetime.now()
    base_date = now.strftime("%Y%m%d")
    
    params = {
        "authKey": api_key,
        "dataType": "JSON",
        "pageNo": "1",
        "numOfRows": "10",  # 테스트용 소량
        "base_date": base_date,
        "base_time": "0200",  # 02시 발표
        "nx": "91",  # 안동 격자 X
        "ny": "106",  # 안동 격자 Y
    }
    
    print(f"\n요청 URL: {endpoint}")
    print(f"파라미터: base_date={base_date}, base_time=0200, nx=91, ny=106\n")
    
    try:
        response = httpx.get(endpoint, params=params, timeout=30)
        print(f"응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 성공! 단기예보 API 권한이 있습니다.")
            data = response.json()
            print(f"\n응답 데이터 샘플:")
            print(f"  Header: {data.get('response', {}).get('header', {})}")
        elif response.status_code == 403:
            print("❌ 403 Forbidden - 단기예보 API 권한이 없습니다!")
            print("\n해결 방법:")
            print("1. https://apihub.kma.go.kr 접속")
            print("2. 마이페이지 → 오픈API 활용 신청")
            print("3. '단기예보조회서비스(VilageFcstInfoService_2.0)' 신청")
            print("4. 승인 대기 (1-2일 소요)")
        else:
            print(f"⚠️  예상치 못한 응답: {response.status_code}")
            print(f"응답 내용: {response.text[:500]}")
    
    except Exception as e:
        print(f"❌ 요청 실패: {e}")

if __name__ == "__main__":
    test_short_permission()
