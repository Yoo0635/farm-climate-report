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
            ("andong-si", "apple"): ResolverRecord(
                lat=36.568,
                lon=128.729,
                kma_grid={"nx": 91, "ny": 106},  # 안동시 격자 좌표
                kma_area_code="11H10000",  # 경상북도 중기육상예보 지역코드
                npms_region_code="47170",
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
