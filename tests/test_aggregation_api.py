"""Tests for the aggregation endpoint and service scaffolding."""

from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from src.api.app import create_app
from src.services.aggregation.aggregator import AggregationService
from src.services.aggregation.models import AggregateProfile, AggregateRequest, ResolvedProfile
from src.services.aggregation.resolver import ProfileResolver
from src.services.aggregation.fetchers import KmaFetcher


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
    assert data["climate"]["daily"], "Expected demo climate daily data"
    assert data["climate"]["provenance"], "Expected provenance entries for climate sources"
    assert any(entry["src"] == "open-meteo" for entry in data["climate"]["daily"])
    assert "pest" not in data, "Structured pest section should be omitted from API response"
    # Evidence text should be present and include the SVC53-filtered style header
    assert data["text"].startswith("=== Non-zero observations for ")
    # Should contain a known demo observation and hints
    assert data["pest_hints"], "Expected pest hints when threshold exceeded"
    assert any("복숭아순나방" in hint for hint in data["pest_hints"])
    assert "복숭아순나방" in data["text"]


def test_aggregation_returns_text_from_npms_only() -> None:
    class StubKma:
        async def fetch(self, resolved: ResolvedProfile) -> dict | None:  # noqa: ARG002
            return None

    class StubOm:
        async def fetch(self, resolved: ResolvedProfile) -> dict | None:  # noqa: ARG002
            return None

    class StubNpms:
        async def fetch(self, resolved: ResolvedProfile) -> dict | None:  # noqa: ARG002
            return {
                "issued_at": "2025-01-01T00:00:00+09:00",
                "crop": "apple",
                "observations": [
                    {"pest": "복숭아순나방", "metric": "트랩당마리수", "code": "SS0127", "value": 11.0, "area": "안동시"}
                ],
                "provenance": "NPMS-SVC53(2025-01-01)",
            }

    async def _run():
        resolver = ProfileResolver()
        service = AggregationService(
            resolver=resolver,
            kma_fetcher=StubKma(),
            open_meteo_fetcher=StubOm(),
            npms_fetcher=StubNpms(),
        )
        request = AggregateRequest(region="Andong-si", crop="apple", stage="flowering")
        return await service.aggregate(request)

    result = asyncio.run(_run())
    assert result.climate.daily == []
    assert result.climate.hourly == []
    assert result.text.startswith("=== Non-zero observations for ")
    assert "복숭아순나방 [SS0127]" in result.text


def test_kma_fetcher_returns_cached_payload() -> None:
    fetcher = KmaFetcher()
    profile = AggregateProfile(region="Andong-si", crop="apple", stage="flowering")
    resolved = ResolvedProfile(profile=profile, lat=36.568, lon=128.729, kma_grid=None, kma_area_code="11H10501", npms_region_code="47170")

    cache_key = fetcher._cache_key(resolved)  # noqa: SLF001 - acceptable for test
    cached_payload = {"issued_at": "2025-01-01T00:00:00+09:00"}
    fetcher._cache[cache_key] = cached_payload  # noqa: SLF001 - acceptable for test

    result = asyncio.run(fetcher.fetch(resolved))
    assert result == cached_payload
