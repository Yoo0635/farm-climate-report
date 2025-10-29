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


def _build_gimcheon_tomato() -> DemoBundle:
    issued_at = datetime(2025, 10, 29, 9, 0, tzinfo=KST)
    provenance_date = issued_at.date().isoformat()

    kma_daily = [
        {"date": "2025-10-29", "tmax_c": 31.2, "tmin_c": 22.5, "precip_mm": 3.0, "wind_ms": 5.1},
        {"date": "2025-10-30", "tmax_c": 32.1, "tmin_c": 23.4, "precip_mm": 0.0, "wind_ms": 4.6},
        {"date": "2025-10-31", "tmax_c": 33.5, "tmin_c": 24.0, "precip_mm": 5.2, "wind_ms": 5.8},
        {"date": "2025-11-01", "tmax_c": 29.8, "tmin_c": 21.7, "precip_mm": 12.3, "wind_ms": 6.4},
    ]

    kma_hourly = []
    start_ts = issued_at.replace(hour=9, minute=0)
    temps = [28.5, 29.3, 30.2, 31.0, 32.5, 33.2, 33.5, 32.8, 31.1, 29.4, 27.8, 26.5]
    rhs = [58, 55, 54, 52, 50, 48, 46, 52, 60, 68, 74, 80]
    winds = [4.2, 4.5, 4.8, 5.1, 5.6, 6.2, 6.5, 6.0, 5.3, 4.8, 4.5, 4.2]
    gusts = [6.8, 7.1, 7.4, 7.6, 8.2, 8.5, 8.7, 8.4, 7.9, 7.2, 6.9, 6.5]
    rain = [0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.4, 0.4, 0.6, 0.8, 1.0, 0.6]
    for idx, temp in enumerate(temps):
        ts = start_ts + timedelta(hours=idx)
        kma_hourly.append(
            {
                "ts": ts.isoformat(),
                "t_c": temp,
                "rh_pct": rhs[idx],
                "wind_ms": winds[idx],
                "gust_ms": gusts[idx],
                "precip_mm": rain[idx],
            }
        )

    kma = {
        "issued_at": issued_at.isoformat(),
        "daily": kma_daily,
        "hourly": kma_hourly,
        "warnings": [
            {
                "type": "HEAT",
                "level": "WATCH",
                "from": (issued_at - timedelta(hours=2)).isoformat(),
                "to": (issued_at + timedelta(hours=10)).isoformat(),
                "area": "경북 김천시",
            }
        ],
        "provenance": f"KMA({provenance_date})",
    }

    om_daily = kma_daily + [
        {"date": "2025-11-02", "tmax_c": 27.4, "tmin_c": 20.9, "precip_mm": 8.5, "wind_ms": 5.9},
        {"date": "2025-11-03", "tmax_c": 26.8, "tmin_c": 19.5, "precip_mm": 0.4, "wind_ms": 4.8},
        {"date": "2025-11-04", "tmax_c": 25.2, "tmin_c": 18.8, "precip_mm": 0.0, "wind_ms": 3.6},
        {"date": "2025-11-05", "tmax_c": 24.6, "tmin_c": 17.9, "precip_mm": 2.2, "wind_ms": 3.8},
        {"date": "2025-11-06", "tmax_c": 23.5, "tmin_c": 16.7, "precip_mm": 0.0, "wind_ms": 3.3},
        {"date": "2025-11-07", "tmax_c": 22.6, "tmin_c": 16.2, "precip_mm": 0.0, "wind_ms": 3.1},
    ]

    om_hourly = []
    for idx in range(24):
        ts = start_ts + timedelta(hours=idx)
        om_hourly.append(
            {
                "ts": ts.isoformat(),
                "t_c": temps[min(idx, len(temps) - 1)] - 0.5,
                "rh_pct": min(95, rhs[min(idx, len(rhs) - 1)] + 4),
                "wind_ms": winds[min(idx, len(winds) - 1)] - 0.3,
                "gust_ms": gusts[min(idx, len(gusts) - 1)] - 0.2,
                "precip_mm": max(0.0, rain[min(idx, len(rain) - 1)] - 0.1),
                "swrad_wm2": 650 if 9 <= (start_ts.hour + idx) % 24 <= 15 else 80,
            }
        )

    open_meteo = {
        "issued_at": (issued_at - timedelta(hours=1)).isoformat(),
        "daily": om_daily,
        "hourly": om_hourly,
        "provenance": f"Open-Meteo({provenance_date})",
    }

    npms = {
        "issued_at": (issued_at - timedelta(days=2)).isoformat(),
        "crop": "tomato",
        "bulletins": [
            {
                "pest": "잿빛곰팡이병",
                "risk": "MODERATE",
                "since": "2025-10-27",
                "summary": "낮 최고 30°C 이상 지속, 시설 내 환기 및 방제 준비 필요",
            },
            {
                "pest": "담배가루이",
                "risk": "LOW",
                "since": "2025-10-25",
                "summary": "고온 다습한 환경에서 밀도가 증가할 수 있어 점검 권장",
            },
        ],
        "provenance": "NPMS(2025-10-27)",
    }

    return DemoBundle(kma=kma, open_meteo=open_meteo, npms=npms)


DEMO_BUNDLES: dict[tuple[str, str], DemoBundle] = {
    ("gimcheon-si", "tomato"): _build_gimcheon_tomato(),
}


def get_demo_bundle(region: str, crop: str) -> DemoBundle | None:
    return DEMO_BUNDLES.get((region.lower(), crop))


__all__ = ["DemoBundle", "get_demo_bundle"]
