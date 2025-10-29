"""Aggregation orchestration: resolve profile, fetch, normalize, and merge data."""

from __future__ import annotations

import asyncio
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
    PestSection,
    WeatherWarning,
)
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

        if payload.demo:
            bundle = get_demo_bundle(profile.region, profile.crop)
            if not bundle:
                raise ValueError(f"No demo data for profile {profile.region}/{profile.crop}")
            return self._assemble(profile, bundle.kma, bundle.open_meteo, bundle.npms)

        resolved = self._resolver.resolve(profile)
        kma_task = asyncio.create_task(self._kma.fetch(resolved))
        om_task = asyncio.create_task(self._open_meteo.fetch(resolved))
        npms_task = asyncio.create_task(self._npms.fetch(resolved))

        kma_data, om_data, npms_data = await asyncio.gather(kma_task, om_task, npms_task, return_exceptions=True)

        errors: list[str] = []
        if isinstance(kma_data, Exception):
            errors.append(f"KMA: {kma_data}")
            kma_data = None
        if isinstance(om_data, Exception):
            errors.append(f"Open-Meteo: {om_data}")
            om_data = None
        if isinstance(npms_data, Exception):
            errors.append(f"NPMS: {npms_data}")
            npms_data = None

        if errors:
            logger.warning("Aggregation fetch errors detected", extra={"errors": errors})

        if not kma_data and not om_data:
            raise RuntimeError("Failed to fetch climate data from both KMA and Open-Meteo.")

        return self._assemble(profile, kma_data, om_data, npms_data)

    def _assemble(
        self,
        profile: AggregateProfile,
        kma_raw: dict | None,
        open_meteo_raw: dict | None,
        npms_raw: dict | None,
    ) -> AggregateEvidencePack:
        kma_norm = self._normalize_kma(kma_raw)
        om_norm = self._normalize_open_meteo(open_meteo_raw)
        npms_norm = self._normalize_npms(npms_raw, profile)

        issued_candidates = [dt for dt in (kma_norm.issued_at, om_norm.issued_at) if dt is not None]
        issued_at = max(issued_candidates) if issued_candidates else datetime.now(tz=KST)

        daily = self._merge_daily(issued_at.date(), kma_norm.daily, om_norm.daily)
        hourly = self._merge_hourly(kma_norm.hourly, om_norm.hourly)
        warnings = kma_norm.warnings
        provenance = [p for p in (kma_norm.provenance, om_norm.provenance) if p]

        climate = ClimateSection(
            horizon_days=max(len(daily) - 1, 0),
            daily=daily,
            hourly=hourly,
            warnings=warnings,
            provenance=provenance,
        )

        pest = npms_norm
        soft_hints = compute_soft_hints(daily=daily, hourly=hourly, warnings=warnings)

        return AggregateEvidencePack(
            profile=profile,
            issued_at=issued_at,
            climate=climate,
            pest=pest,
            soft_hints=soft_hints,
        )

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

    def _normalize_npms(self, data: dict | None, profile: AggregateProfile) -> PestSection:
        bulletins: list[PestBulletin] = []
        provenance = []

        if data:
            provenance_value = data.get("provenance")
            if provenance_value:
                provenance.append(provenance_value)

            for entry in data.get("bulletins", []) or []:
                bulletins.append(
                    PestBulletin(
                        pest=entry.get("pest", ""),
                        risk=entry.get("risk", "LOW"),
                        since=_coerce_date(entry.get("since")),
                        summary=entry.get("summary", ""),
                    )
                )

        return PestSection(crop=profile.crop, bulletins=bulletins, provenance=provenance)

    def _merge_daily(
        self,
        base_date: date,
        kma_daily: Iterable[ClimateDaily],
        open_meteo_daily: Iterable[ClimateDaily],
    ) -> list[ClimateDaily]:
        kma_map = {entry.date: entry for entry in kma_daily}
        om_map = {entry.date: entry for entry in open_meteo_daily}

        all_dates = sorted(set(kma_map) | set(om_map))
        if not all_dates:
            all_dates = [base_date + timedelta(days=i) for i in range(11)]

        horizon: list[ClimateDaily] = []
        for offset in range(0, 11):
            day = base_date + timedelta(days=offset)
            entry: ClimateDaily | None = None
            if offset <= 3:
                entry = kma_map.get(day) or om_map.get(day)
            else:
                entry = om_map.get(day) or kma_map.get(day)
            if entry:
                horizon.append(entry)
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


def _coerce_datetime(value) -> datetime | None:  # noqa: ANN001 - dynamic typing for coercion
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
