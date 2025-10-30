"""Scripted demo datasets for the aggregation endpoint."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


@dataclass(frozen=True)
class DemoBundle:
    kma: dict
    open_meteo: dict
    npms: dict
def _build_andong_apple() -> DemoBundle:
    issued_at = datetime(2025, 10, 30, 6, 0, tzinfo=KST)
    base_date = issued_at.date().isoformat()

    kma_daily = [
        {"date": "2025-11-02", "summary": "맑음", "precip_probability_pct": 10.0},
        {"date": "2025-11-03", "summary": "맑음 / 구름많음", "precip_probability_pct": 20.0},
        {"date": "2025-11-04", "summary": "구름많음", "precip_probability_pct": 30.0},
        {"date": "2025-11-05", "summary": "흐림", "precip_probability_pct": 40.0},
        {"date": "2025-11-06", "summary": "흐리고 비", "precip_probability_pct": 60.0},
        {"date": "2025-11-07", "summary": "구름많음", "precip_probability_pct": 30.0},
        {"date": "2025-11-08", "summary": "맑음", "precip_probability_pct": 10.0},
    ]

    kma = {
        "issued_at": issued_at.isoformat(),
        "daily": kma_daily,
        "hourly": [],
        "warnings": [],
        "provenance": f"KMA({base_date})",
    }

    om_daily = [
        {"date": "2025-10-30", "tmax_c": 21.5, "tmin_c": 8.2, "precip_mm": 0.0, "wind_ms": 2.8},
        {"date": "2025-10-31", "tmax_c": 22.1, "tmin_c": 9.0, "precip_mm": 0.0, "wind_ms": 3.1},
        {"date": "2025-11-01", "tmax_c": 21.0, "tmin_c": 8.5, "precip_mm": 0.4, "wind_ms": 2.5},
        {"date": "2025-11-02", "tmax_c": 20.4, "tmin_c": 7.8, "precip_mm": 0.0, "wind_ms": 2.9},
        {"date": "2025-11-03", "tmax_c": 19.8, "tmin_c": 6.9, "precip_mm": 0.0, "wind_ms": 2.7},
        {"date": "2025-11-04", "tmax_c": 18.6, "tmin_c": 6.5, "precip_mm": 1.2, "wind_ms": 2.4},
        {"date": "2025-11-05", "tmax_c": 17.2, "tmin_c": 5.9, "precip_mm": 3.0, "wind_ms": 3.0},
        {"date": "2025-11-06", "tmax_c": 18.8, "tmin_c": 6.7, "precip_mm": 0.6, "wind_ms": 2.6},
        {"date": "2025-11-07", "tmax_c": 19.5, "tmin_c": 7.1, "precip_mm": 0.0, "wind_ms": 2.3},
        {"date": "2025-11-08", "tmax_c": 20.3, "tmin_c": 7.5, "precip_mm": 0.0, "wind_ms": 2.1},
        {"date": "2025-11-09", "tmax_c": 21.0, "tmin_c": 8.0, "precip_mm": 0.0, "wind_ms": 2.4},
    ]

    om_hourly = []
    start_ts = issued_at.replace(hour=6, minute=0)
    temps = [12.0, 12.5, 13.4, 15.0, 17.2, 19.1, 20.5, 21.3, 20.8, 18.9, 16.4, 14.2]
    rhs = [80, 78, 75, 68, 60, 55, 52, 50, 54, 62, 70, 78]
    winds = [2.4, 2.6, 2.8, 3.0, 3.1, 3.2, 3.3, 3.2, 3.0, 2.8, 2.6, 2.4]
    for idx in range(12):
        ts = start_ts + timedelta(hours=idx)
        om_hourly.append(
            {
                "ts": ts.isoformat(),
                "t_c": temps[idx],
                "rh_pct": rhs[idx],
                "wind_ms": winds[idx],
                "gust_ms": winds[idx] + 0.6,
                "precip_mm": 0.0,
                "swrad_wm2": 400 if 9 <= ts.hour <= 15 else 50,
            }
        )

    open_meteo = {
        "issued_at": (issued_at - timedelta(hours=1)).isoformat(),
        "daily": om_daily,
        "hourly": om_hourly,
        "provenance": f"Open-Meteo({base_date})",
    }

    npms = {
        "issued_at": (issued_at - timedelta(days=1)).isoformat(),
        "crop": "apple",
        "bulletins": [
            {
                "pest": "갈색무늬병",
                "risk": "MODERATE",
                "since": "2025-10-28",
                "summary": "강수 이후 전엽기 과원은 예방 살포 및 환기 강화",
            },
            {
                "pest": "탄저병",
                "risk": "LOW",
                "since": "2025-10-25",
                "summary": "일교차 큰 기간 꽃눈 주변 병반 점검",
            },
        ],
        "observations": [
            {
                "pest": "사과굴나방",
                "metric": "트랩당마리수",
                "code": "SS0128",
                "value": 92.4,
                "area": "안동시",
            },
            {
                "pest": "갈색무늬병",
                "metric": "병든잎률",
                "code": "SS0101",
                "value": 0.0,
                "area": "안동시",
            },
        ],
        "provenance": ["NPMS(2025-10-29)", "NPMS-SVC53(2025-10-29)"],
    }

    return DemoBundle(kma=kma, open_meteo=open_meteo, npms=npms)


DEMO_BUNDLES: dict[tuple[str, str], DemoBundle] = {
    ("andong-si", "apple"): _build_andong_apple(),
}


def get_demo_bundle(region: str, crop: str) -> DemoBundle | None:
    return DEMO_BUNDLES.get((region.lower(), crop))


__all__ = ["DemoBundle", "get_demo_bundle"]
