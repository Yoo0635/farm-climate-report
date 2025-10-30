"""Aggregation orchestration: resolve profile, fetch, normalize, and merge data."""

from __future__ import annotations

import asyncio
import os
import logging
from datetime import date, datetime, timedelta
from typing import Iterable
from zoneinfo import ZoneInfo

from src.services.aggregation.demo import get_demo_bundle
from src.services.aggregation.fetchers import KmaFetcher, NpmsFetcher, OpenMeteoFetcher
from src.services.aggregation.models import (
    AggregateEvidencePack,
    AggregateProfile,
    AggregateRequest,
    ClimateDaily,
    ClimateHourly,
    ClimateSection,
    PestBulletin,
    PestObservation,
    PestSection,
    WeatherWarning,
)
from src.services.aggregation.pest_hints import compute_pest_hints
from src.services.aggregation.resolver import ProfileResolver
from src.services.aggregation.soft_hints import compute_soft_hints

logger = logging.getLogger(__name__)
KST = ZoneInfo("Asia/Seoul")


class AggregationService:
    """Coordinate aggregation of multiple climate/pest data sources."""

    def __init__(
        self,
        resolver: ProfileResolver | None = None,
        kma_fetcher: KmaFetcher | None = None,
        open_meteo_fetcher: OpenMeteoFetcher | None = None,
        npms_fetcher: NpmsFetcher | None = None,
    ) -> None:
        self._resolver = resolver or ProfileResolver()
        self._kma = kma_fetcher or KmaFetcher()
        self._open_meteo = open_meteo_fetcher or OpenMeteoFetcher()
        self._npms = npms_fetcher or NpmsFetcher()

    async def aggregate(self, payload: AggregateRequest) -> AggregateEvidencePack:
        profile = AggregateProfile(region=payload.region, crop=payload.crop, stage=payload.stage)
        resolved = self._resolver.resolve(profile)

        # DEMO: build from scripted bundle so we can showcase full climate+pest output offline.
        if payload.demo:
            bundle = get_demo_bundle(profile.region, profile.crop)
            if not bundle:
                raise ValueError(f"No demo data for profile {profile.region}/{profile.crop}")
            kma_norm = self._normalize_kma(bundle.kma)
            om_norm = self._normalize_open_meteo(bundle.open_meteo)
            npms_norm = self._normalize_npms(bundle.npms, profile)
            climate = self._build_climate_section(
                base_date=self._determine_base_date(om_norm, kma_norm),
                kma_norm=kma_norm,
                open_meteo_norm=om_norm,
            )
            text = self._format_npms_text(npms_norm, region_code=resolved.npms_region_code)
            pest_hints = compute_pest_hints(npms_norm.observations)
            issued_at = self._select_issued_at(
                kma_norm.issued_at,
                om_norm.issued_at,
                _coerce_datetime(bundle.npms.get("issued_at")) if isinstance(bundle.npms, dict) else None,
            )
            soft_hints = compute_soft_hints(climate.daily, climate.hourly, climate.warnings) if (
                climate.daily or climate.hourly or climate.warnings
            ) else None
            return AggregateEvidencePack(
                profile=profile,
                issued_at=issued_at,
                climate=climate,
                pest=npms_norm,
                text=text,
                pest_hints=pest_hints,
                soft_hints=soft_hints,
            )

        # LIVE: fetch KMA, Open-Meteo, and NPMS in parallel with graceful degradation.
        kma_task = asyncio.create_task(self._kma.fetch(resolved))
        om_task = asyncio.create_task(self._open_meteo.fetch(resolved))
        npms_task = asyncio.create_task(self._npms.fetch(resolved))

        kma_raw, om_raw, npms_raw = await asyncio.gather(
            kma_task,
            om_task,
            npms_task,
            return_exceptions=True,
        )

        if isinstance(kma_raw, Exception):
            logger.warning("KMA fetch failed: %s", kma_raw)
            kma_raw = None
        if isinstance(om_raw, Exception):
            logger.warning("Open-Meteo fetch failed: %s", om_raw)
            om_raw = None
        if isinstance(npms_raw, Exception):
            logger.warning("NPMS fetch failed: %s", npms_raw)
            npms_raw = None

        kma_norm = self._normalize_kma(kma_raw if isinstance(kma_raw, dict) else None)
        om_norm = self._normalize_open_meteo(om_raw if isinstance(om_raw, dict) else None)
        npms_norm = self._normalize_npms(npms_raw if isinstance(npms_raw, dict) else None, profile)

        climate = self._build_climate_section(
            base_date=self._determine_base_date(om_norm, kma_norm),
            kma_norm=kma_norm,
            open_meteo_norm=om_norm,
        )
        text = self._format_npms_text(npms_norm, region_code=resolved.npms_region_code)
        pest_hints = compute_pest_hints(npms_norm.observations)
        issued_at = self._select_issued_at(
            kma_norm.issued_at,
            om_norm.issued_at,
            _coerce_datetime(npms_raw.get("issued_at")) if isinstance(npms_raw, dict) else None,
        )
        soft_hints = compute_soft_hints(climate.daily, climate.hourly, climate.warnings) if (
            climate.daily or climate.hourly or climate.warnings
        ) else None

        return AggregateEvidencePack(
            profile=profile,
            issued_at=issued_at,
            climate=climate,
            pest=npms_norm,
            text=text,
            pest_hints=pest_hints,
            soft_hints=soft_hints,
        )

    def _determine_base_date(self, open_meteo_norm: _NormalizedSource, kma_norm: _NormalizedSource) -> date:
        if open_meteo_norm.daily:
            return open_meteo_norm.daily[0].date
        if kma_norm.daily:
            return kma_norm.daily[0].date
        return datetime.now(tz=KST).date()

    def _build_climate_section(
        self,
        *,
        base_date: date,
        kma_norm: _NormalizedSource,
        open_meteo_norm: _NormalizedSource,
    ) -> ClimateSection:
        daily = (
            self._merge_daily(base_date, kma_norm.daily, open_meteo_norm.daily)
            if (kma_norm.daily or open_meteo_norm.daily)
            else []
        )
        hourly = self._merge_hourly(kma_norm.hourly, open_meteo_norm.hourly)
        warnings = kma_norm.warnings
        provenance: list[str] = []
        if kma_norm.provenance:
            provenance.append(kma_norm.provenance)
        if open_meteo_norm.provenance:
            provenance.append(open_meteo_norm.provenance)
        horizon = max(0, len(daily) - 1) if daily else 0
        return ClimateSection(
            horizon_days=horizon,
            daily=daily,
            hourly=hourly,
            warnings=warnings,
            provenance=provenance,
        )

    def _select_issued_at(self, *candidates: datetime | None) -> datetime:
        valid = [dt for dt in candidates if dt is not None]
        if valid:
            return max(valid)
        return datetime.now(tz=KST)

    def _format_npms_text(self, pest: PestSection, *, region_code: str | None) -> str:
        target_name = "안동시"
        target_code = os.environ.get("NPMS_TARGET_SIGUNGU_CODE") or (region_code[:4] if region_code else "-")
        header = f"=== Non-zero observations for {target_name} ({target_code}) ==="
        lines: list[str] = [header]
        if not pest.observations:
            lines.append("(none)")
            return "\n".join(lines)
        for idx, o in enumerate(pest.observations, start=1):
            value_str = "" if o.value is None else f"{o.value}"
            lines.append(f"{idx}. {o.pest} [{o.code}] = {value_str} (area: {o.area})")
        return "\n".join(lines)

    def _normalize_kma(self, data: dict | None):
        issued_at: datetime | None = None
        daily: list[ClimateDaily] = []
        hourly: list[ClimateHourly] = []
        warnings: list[WeatherWarning] = []
        provenance: str | None = None

        if not data:
            return _NormalizedSource(issued_at, daily, hourly, warnings, provenance)

        issued_at = _coerce_datetime(data.get("issued_at"))

        for entry in data.get("daily", []) or []:
            daily.append(
                ClimateDaily(
                    date=_coerce_date(entry.get("date")),
                    tmax_c=_coerce_float(entry.get("tmax_c")),
                    tmin_c=_coerce_float(entry.get("tmin_c")),
                    precip_mm=_coerce_float(entry.get("precip_mm")),
                    wind_ms=_coerce_float(entry.get("wind_ms")),
                    summary=entry.get("summary"),
                    precip_probability_pct=_coerce_float(
                        entry.get("precip_probability_pct")
                    ),
                    src="kma",
                )
            )

        for entry in data.get("hourly", []) or []:
            hourly.append(
                ClimateHourly(
                    ts=_coerce_datetime(entry.get("ts")),
                    t_c=_coerce_float(entry.get("t_c")),
                    rh_pct=_coerce_float(entry.get("rh_pct")),
                    wind_ms=_coerce_float(entry.get("wind_ms")),
                    gust_ms=_coerce_float(entry.get("gust_ms")),
                    precip_mm=_coerce_float(entry.get("precip_mm")),
                    src="kma",
                )
            )

        for entry in data.get("warnings", []) or []:
            warnings.append(
                WeatherWarning(
                    type=entry.get("type", "HEAT"),
                    level=entry.get("level", "WATCH"),
                    area=entry.get("area", ""),
                    from_=_coerce_datetime(entry.get("from")),
                    to=_coerce_datetime(entry.get("to")),
                )
            )

        provenance = data.get("provenance")

        return _NormalizedSource(issued_at, daily, hourly, warnings, provenance)

    def _normalize_open_meteo(self, data: dict | None):
        issued_at: datetime | None = None
        daily: list[ClimateDaily] = []
        hourly: list[ClimateHourly] = []
        provenance: str | None = None

        if not data:
            return _NormalizedSource(issued_at, daily, hourly, [], provenance)

        issued_at = _coerce_datetime(data.get("issued_at"))

        for entry in data.get("daily", []) or []:
            daily.append(
                ClimateDaily(
                    date=_coerce_date(entry.get("date")),
                    tmax_c=_coerce_float(entry.get("tmax_c")),
                    tmin_c=_coerce_float(entry.get("tmin_c")),
                    precip_mm=_coerce_float(entry.get("precip_mm")),
                    wind_ms=_coerce_float(entry.get("wind_ms")),
                    summary=entry.get("summary"),
                    precip_probability_pct=_coerce_float(
                        entry.get("precip_probability_pct")
                    ),
                    src="open-meteo",
                )
            )

        for entry in data.get("hourly", []) or []:
            hourly.append(
                ClimateHourly(
                    ts=_coerce_datetime(entry.get("ts")),
                    t_c=_coerce_float(entry.get("t_c")),
                    rh_pct=_coerce_float(entry.get("rh_pct")),
                    wind_ms=_coerce_float(entry.get("wind_ms")),
                    gust_ms=_coerce_float(entry.get("gust_ms")),
                    precip_mm=_coerce_float(entry.get("precip_mm")),
                    swrad_wm2=_coerce_float(entry.get("swrad_wm2")),
                    src="open-meteo",
                )
            )

        provenance = data.get("provenance")

        return _NormalizedSource(issued_at, daily, hourly, [], provenance)

    def _normalize_npms(
        self, data: dict | None, profile: AggregateProfile
    ) -> PestSection:
        bulletins: list[PestBulletin] = []
        observations: list[PestObservation] = []
        provenance = []

        if data:
            provenance_value = data.get("provenance")
            if isinstance(provenance_value, str):
                provenance.append(provenance_value)
            elif isinstance(provenance_value, list):
                provenance.extend(str(item) for item in provenance_value if item)

            for entry in data.get("bulletins", []) or []:
                bulletins.append(
                    PestBulletin(
                        pest=entry.get("pest", ""),
                        risk=entry.get("risk", "LOW"),
                        since=_coerce_date(entry.get("since")),
                        summary=entry.get("summary", ""),
                    )
                )

            for entry in data.get("observations", []) or []:
                observations.append(
                    PestObservation(
                        pest=entry.get("pest", ""),
                        metric=entry.get("metric", ""),
                        code=entry.get("code", ""),
                        value=_coerce_float(entry.get("value")),
                        area=entry.get("area", ""),
                        unit=entry.get("unit"),
                    )
                )

        return PestSection(
            crop=profile.crop,
            bulletins=bulletins,
            observations=observations,
            provenance=provenance,
        )

    def _merge_daily(
        self,
        base_date: date,
        kma_daily: Iterable[ClimateDaily],
        open_meteo_daily: Iterable[ClimateDaily],
    ) -> list[ClimateDaily]:
        kma_map = {entry.date: entry for entry in kma_daily}
        om_map = {entry.date: entry for entry in open_meteo_daily}

        horizon: list[ClimateDaily] = []
        for offset in range(0, 11):
            day = base_date + timedelta(days=offset)
            om_entry = om_map.get(day)
            kma_entry = kma_map.get(day)
            if om_entry:
                if kma_entry:
                    if kma_entry.summary and not om_entry.summary:
                        om_entry.summary = kma_entry.summary
                    if (
                        kma_entry.precip_probability_pct is not None
                        and om_entry.precip_probability_pct is None
                    ):
                        om_entry.precip_probability_pct = (
                            kma_entry.precip_probability_pct
                        )
                horizon.append(om_entry)
            elif kma_entry:
                horizon.append(kma_entry)
        if not horizon:
            return []
        return horizon

    def _merge_hourly(
        self,
        kma_hourly: Iterable[ClimateHourly],
        open_meteo_hourly: Iterable[ClimateHourly],
    ) -> list[ClimateHourly]:
        kma_map = {entry.ts: entry for entry in kma_hourly}
        om_map = {entry.ts: entry for entry in open_meteo_hourly}

        if not kma_map and not om_map:
            return []

        timestamps = sorted(set(kma_map) | set(om_map))
        start = min(timestamps)
        limit = start + timedelta(hours=72)

        merged: list[ClimateHourly] = []
        for ts in timestamps:
            if ts >= limit:
                break
            entry = kma_map.get(ts) or om_map.get(ts)
            if entry:
                merged.append(entry)
        return merged


def _coerce_float(value) -> float | None:  # noqa: ANN001 - dynamic typing for coercion
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_datetime(
    value,
) -> datetime | None:  # noqa: ANN001 - dynamic typing for coercion
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=KST)
    else:
        dt = dt.astimezone(KST)
    return dt


def _coerce_date(value) -> date:  # noqa: ANN001 - dynamic typing for coercion
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.astimezone(KST).date()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    return datetime.now(tz=KST).date()


class _NormalizedSource:
    def __init__(
        self,
        issued_at: datetime | None,
        daily: list[ClimateDaily],
        hourly: list[ClimateHourly],
        warnings: list[WeatherWarning],
        provenance: str | None,
    ) -> None:
        self.issued_at = issued_at
        self.daily = daily
        self.hourly = hourly
        self.warnings = warnings
        self.provenance = provenance


_service_instance: AggregationService | None = None


def get_aggregation_service() -> AggregationService:
    global _service_instance
    if _service_instance is None:
        _service_instance = AggregationService()
    return _service_instance
