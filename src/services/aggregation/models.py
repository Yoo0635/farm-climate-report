"""Pydantic models for the aggregation service."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


SUPPORTED_CROPS = ("apple",)


class AggregateProfile(BaseModel):
    """Minimal profile required to drive aggregation."""

    region: str = Field(..., min_length=1)
    crop: Literal["apple"]
    stage: str = Field(..., min_length=1)


class AggregateRequest(AggregateProfile):
    """API request payload."""

    demo: bool = Field(False, description="If true, return scripted demo data instead of live fetches.")


class ResolvedProfile(BaseModel):
    """Profile enriched with IDs required by the upstream APIs."""

    model_config = ConfigDict(frozen=True)

    profile: AggregateProfile
    lat: float
    lon: float
    kma_grid: dict[str, int] | None = None
    kma_area_code: str | None = None
    npms_region_code: str | None = None


class ClimateDaily(BaseModel):
    date: date
    tmax_c: float | None = None
    tmin_c: float | None = None
    precip_mm: float | None = None
    wind_ms: float | None = None
    summary: str | None = None
    precip_probability_pct: float | None = None
    src: Literal["kma", "open-meteo"] | None = None


class ClimateHourly(BaseModel):
    ts: datetime
    t_c: float | None = None
    rh_pct: float | None = None
    wind_ms: float | None = None
    gust_ms: float | None = None
    precip_mm: float | None = None
    swrad_wm2: float | None = None
    src: Literal["kma", "open-meteo"] | None = None


class WeatherWarning(BaseModel):
    """Warning payload (always sourced from KMA)."""

    model_config = ConfigDict(populate_by_name=True)

    type: Literal["HEAT", "RAIN", "WIND", "COLD", "TYPHOON"]
    level: Literal["WATCH", "WARNING"]
    area: str
    source: Literal["kma"] = "kma"
    from_: datetime = Field(..., alias="from")
    to: datetime


class ClimateSection(BaseModel):
    horizon_days: int
    daily: list[ClimateDaily]
    hourly: list[ClimateHourly]
    warnings: list[WeatherWarning]
    provenance: list[str]


class PestBulletin(BaseModel):
    pest: str
    risk: Literal["LOW", "MODERATE", "HIGH", "ALERT"]
    since: date
    summary: str


class PestSection(BaseModel):
    crop: Literal["apple"]
    bulletins: list[PestBulletin]
    provenance: list[str]


class SoftHints(BaseModel):
    rain_run_max_days: int | None = None
    heat_hours_ge_33c: int | None = None
    wind_hours_ge_10ms: int | None = None
    wet_nights_count: int | None = None
    diurnal_range_max: float | None = None
    first_warning_type: Literal["HEAT", "RAIN", "WIND", "COLD", "TYPHOON"] | None = None


class AggregateEvidencePack(BaseModel):
    profile: AggregateProfile
    issued_at: datetime
    climate: ClimateSection
    pest: PestSection
    soft_hints: SoftHints | None = None
