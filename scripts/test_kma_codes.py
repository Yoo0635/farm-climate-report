#!/usr/bin/env python3
"""Test which KMA APIs accept which region codes."""

import json
import os
import sys
from urllib.parse import urlencode
from urllib.request import urlopen

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

KMA_KEY = os.environ.get("KMA_API_KEY")
BASE_URL = "https://apihub.kma.go.kr/api/typ02/openApi"

def test_mid_land(reg_id: str) -> dict:
    """중기육상예보 - 광역만"""
    params = {
        "authKey": KMA_KEY,
        "dataType": "JSON",
        "pageNo": "1",
        "numOfRows": "10",
        "regId": reg_id,
        "tmFc": "202510301800",  # 임의 시각
    }
    url = f"{BASE_URL}/MidFcstInfoService/getMidLandFcst?{urlencode(params)}"
    try:
        with urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

def test_mid_ta(reg_id: str) -> dict:
    """중기기온예보 - 시/군/구 가능"""
    params = {
        "authKey": KMA_KEY,
        "dataType": "JSON",
        "pageNo": "1",
        "numOfRows": "10",
        "regId": reg_id,
        "tmFc": "202510301800",
    }
    url = f"{BASE_URL}/MidFcstInfoService/getMidTa?{urlencode(params)}"
    try:
        with urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

def main():
    if not KMA_KEY:
        print("ERROR: KMA_API_KEY not set", file=sys.stderr)
        return 1
    
    codes_to_test = {
        "11H10000": "경상북도 (광역)",
        "11H10501": "안동 (시/군/구)",
        "11D10000": "경상북도 (다른 광역 코드)",
    }
    
    for code, name in codes_to_test.items():
        print(f"\n{'='*60}")
        print(f"Testing: {code} ({name})")
        print(f"{'='*60}")
        
        print(f"\n--- getMidLandFcst (중기육상예보) ---")
        result = test_mid_land(code)
        header = result.get("response", {}).get("header", {})
        print(f"Result Code: {header.get('resultCode')}")
        print(f"Result Msg: {header.get('resultMsg')}")
        
        print(f"\n--- getMidTa (중기기온예보) ---")
        result = test_mid_ta(code)
        header = result.get("response", {}).get("header", {})
        print(f"Result Code: {header.get('resultCode')}")
        print(f"Result Msg: {header.get('resultMsg')}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
