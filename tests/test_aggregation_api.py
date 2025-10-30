"""Tests for the aggregation endpoint and service scaffolding."""

from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from src.api.app import create_app
from src.services.aggregation.aggregator import AggregationService
from src.services.aggregation.fetchers import KmaFetcher
from src.services.aggregation.models import (
    AggregateProfile,
    AggregateRequest,
    ResolvedProfile,
)
from src.services.aggregation.resolver import ProfileResolver


def _create_client() -> TestClient:
    return TestClient(create_app())


def test_aggregate_demo_succeeds() -> None:
    client = _create_client()
    payload = {"region": "Andong-si", "crop": "apple", "stage": "flowering"}

    response = client.post("/api/aggregate?demo=true", json=payload)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["profile"]["region"] == "Andong-si"
    assert data["profile"]["crop"] == "apple"
    assert data["climate"]["daily"], "Expected daily data in response"
    first_day = data["climate"]["daily"][0]
    assert first_day["src"] == "open-meteo"
    assert any(day.get("summary") for day in data["climate"]["daily"])
    assert data["pest"]["observations"], "Expected pest observations in demo payload"
    assert data["soft_hints"]["rain_run_max_days"] >= 1


def test_aggregation_falls_back_to_open_meteo_when_kma_missing() -> None:
    class StubFetcher:
        def __init__(self, payload: dict | None) -> None:
            self.payload = payload
            self.calls = 0

        async def fetch(
            self, resolved: ResolvedProfile
        ) -> dict | None:  # noqa: ARG002 - fixture signature
            self.calls += 1
            return self.payload

    open_meteo_payload = {
        "issued_at": "2025-01-01T00:00:00+09:00",
        "daily": [
            {
                "date": "2025-01-01",
                "tmax_c": 18.0,
                "tmin_c": 5.0,
                "precip_mm": 0.0,
                "wind_ms": 3.0,
            },
            {
                "date": "2025-01-02",
                "tmax_c": 17.5,
                "tmin_c": 4.5,
                "precip_mm": 0.6,
                "wind_ms": 2.8,
            },
        ],
        "hourly": [
            {
                "ts": "2025-01-01T00:00:00+09:00",
                "t_c": 6.0,
                "rh_pct": 65,
                "wind_ms": 2.4,
                "precip_mm": 0.0,
            },
            {
                "ts": "2025-01-01T01:00:00+09:00",
                "t_c": 5.8,
                "rh_pct": 67,
                "wind_ms": 2.6,
                "precip_mm": 0.0,
            },
        ],
        "provenance": "Open-Meteo(2025-01-01)",
    }

    npms_payload = {
        "issued_at": "2024-12-31T00:00:00+09:00",
        "crop": "apple",
        "bulletins": [],
        "provenance": "NPMS(2024-12-31)",
    }

    async def _run():
        resolver = ProfileResolver()
        service = AggregationService(
            resolver=resolver,
            kma_fetcher=StubFetcher(None),
            open_meteo_fetcher=StubFetcher(open_meteo_payload),
            npms_fetcher=StubFetcher(npms_payload),
        )

        request = AggregateRequest(region="Andong-si", crop="apple", stage="flowering")
        return await service.aggregate(request)

    result = asyncio.run(_run())

    assert any(src.startswith("Open-Meteo") for src in result.climate.provenance)
    assert all(day.src == "open-meteo" for day in result.climate.daily)
    assert result.climate.warnings == []


def test_kma_fetcher_returns_cached_payload() -> None:
    fetcher = KmaFetcher()
    profile = AggregateProfile(region="Andong-si", crop="apple", stage="flowering")
    resolved = ResolvedProfile(
        profile=profile,
        lat=36.568,
        lon=128.729,
        kma_grid=None,
        kma_area_code="11H10501",
        npms_region_code="47170",
    )

    cache_key = fetcher._cache_key(resolved)  # noqa: SLF001 - acceptable for test
    cached_payload = {"issued_at": "2025-01-01T00:00:00+09:00"}
    fetcher._cache[cache_key] = cached_payload  # noqa: SLF001 - acceptable for test

    result = asyncio.run(fetcher.fetch(resolved))
    assert result == cached_payload
