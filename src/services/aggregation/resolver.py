"""Profile resolver mapping region/crop to API identifiers."""

from __future__ import annotations

from dataclasses import dataclass

from src.services.aggregation.models import AggregateProfile, ResolvedProfile


@dataclass(frozen=True)
class ResolverRecord:
    lat: float
    lon: float
    kma_grid: dict[str, int] | None
    kma_area_code: str | None
    npms_region_code: str | None


class ProfileResolver:
    """Very small in-memory resolver for the hackathon demo."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], ResolverRecord] = {
            ("gimcheon-si", "tomato"): ResolverRecord(
                lat=36.137,
                lon=128.113,
                kma_grid={"nx": 83, "ny": 97},
                kma_area_code="11G00701",
                npms_region_code="47280",
            ),
            ("hwaseong-si", "rice"): ResolverRecord(
                lat=37.199,
                lon=126.832,
                kma_grid={"nx": 55, "ny": 123},
                kma_area_code="11B20601",
                npms_region_code="41280",
            ),
            ("jeju-si", "lettuce"): ResolverRecord(
                lat=33.499,
                lon=126.531,
                kma_grid={"nx": 52, "ny": 38},
                kma_area_code="11G00201",
                npms_region_code="50110",
            ),
        }

    def resolve(self, profile: AggregateProfile) -> ResolvedProfile:
        key = (profile.region.lower(), profile.crop)
        record = self._records.get(key)
        if not record:
            raise ValueError(f"Unsupported region/crop combination: {profile.region} / {profile.crop}")

        return ResolvedProfile(
            profile=profile,
            lat=record.lat,
            lon=record.lon,
            kma_grid=record.kma_grid,
            kma_area_code=record.kma_area_code,
            npms_region_code=record.npms_region_code,
        )


__all__ = ["ProfileResolver"]
