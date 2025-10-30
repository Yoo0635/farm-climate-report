"""Deterministic helper calculations for optional soft hints."""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from src.services.aggregation.models import ClimateDaily, ClimateHourly, SoftHints, WeatherWarning


def compute_soft_hints(
    daily: list[ClimateDaily],
    hourly: list[ClimateHourly],
    warnings: list[WeatherWarning],
) -> SoftHints:
    return SoftHints(
        rain_run_max_days=_rain_run_max_days(daily),
        heat_hours_ge_33c=_count_hours(hourly, field="t_c", threshold=33.0),
        wind_hours_ge_10ms=_count_hours(hourly, field="wind_ms", threshold=10.0),
        wet_nights_count=_wet_nights(hourly),
        diurnal_range_max=_diurnal_range_max(daily),
        first_warning_type=warnings[0].type if warnings else None,
    )


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


__all__ = ["compute_soft_hints"]
