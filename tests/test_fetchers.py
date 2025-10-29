"""Unit tests for aggregation fetchers."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
import pytest

from src.services.aggregation.fetchers import KmaFetcher, NpmsFetcher, OpenMeteoFetcher
from src.services.aggregation.models import AggregateProfile, ResolvedProfile

KST = ZoneInfo("Asia/Seoul")


def _resolved_profile(crop: str = "rice") -> ResolvedProfile:
    profile = AggregateProfile(region="Gimcheon-si", crop=crop, stage="test-stage")
    return ResolvedProfile(
        profile=profile,
        lat=36.137,
        lon=128.113,
        kma_grid={"nx": 83, "ny": 97},
        kma_area_code="11B00000",
        npms_region_code="41280",
    )


def test_open_meteo_fetcher_parses_payload() -> None:
    async def _run() -> None:
        fetcher = OpenMeteoFetcher()

        start = datetime(2025, 10, 30, 0, 0)
        hours = [(start + timedelta(hours=hour)).strftime("%Y-%m-%dT%H:%M") for hour in range(75)]
        hourly_payload = {
            "time": hours,
            "temperature_2m": [20.0 + (hour * 0.1) for hour in range(75)],
            "relative_humidity_2m": [60 for _ in range(75)],
            "wind_speed_10m": [10 for _ in range(75)],
            "wind_gusts_10m": [15 for _ in range(75)],
            "precipitation": [0.5 for _ in range(75)],
            "shortwave_radiation": [500 for _ in range(75)],
        }
        daily_payload = {
            "time": ["2025-10-30", "2025-10-31"],
            "temperature_2m_max": [25.1, 24.9],
            "temperature_2m_min": [17.2, 16.8],
            "precipitation_sum": [4.2, 0.0],
            "windspeed_10m_max": [18.0, 10.8],
        }

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path.endswith("/v1/forecast")
            return httpx.Response(200, json={"daily": daily_payload, "hourly": hourly_payload})

        fetcher._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))  # noqa: SLF001 - testing internal override
        result = await fetcher.fetch(_resolved_profile())
        await fetcher.aclose()

        assert result is not None
        assert len(result["daily"]) == 2
        assert result["daily"][0]["tmax_c"] == 25.1
        assert len(result["hourly"]) == 72  # limited to next 72 hours
        assert result["hourly"][0]["ts"].endswith("+09:00")
        assert result["hourly"][0]["wind_ms"] == pytest.approx(10 / 3.6)

    asyncio.run(_run())


def test_kma_fetcher_parses_mid_land() -> None:
    async def _run() -> None:
        class StubKmaFetcher(KmaFetcher):
            def _candidate_tmfc(self) -> list[datetime]:
                return [datetime(2025, 10, 29, 6, tzinfo=KST)]

        fetcher = StubKmaFetcher(auth_key="dummy-key")

        mid_payload = {
            "response": {
                "header": {"resultCode": "00", "resultMsg": "NORMAL_SERVICE"},
                "body": {
                    "items": {
                        "item": [
                            {
                                "regId": "11B00000",
                                "wf4Am": "Sunny",
                                "wf4Pm": "Cloudy",
                                "rnSt4Am": 10,
                                "rnSt4Pm": 20,
                                "wf5Am": "Overcast",
                                "wf5Pm": "Rain",
                                "rnSt5Am": 30,
                                "rnSt5Pm": 40,
                                "wf8": "Sunny",
                                "rnSt8": 50,
                            }
                        ]
                    }
                },
            }
        }

        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=mid_payload)

        fetcher._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))  # noqa: SLF001 - testing internal override
        result = await fetcher.fetch(_resolved_profile())
        await fetcher.aclose()

        assert result is not None
        assert result["daily"][0]["date"] == "2025-11-01"
        assert result["daily"][0]["summary"] == "Sunny / Cloudy"
        assert result["daily"][0]["precip_mm"] is None
        assert result["daily"][0]["precip_probability_pct"] == 15.0
        assert result["provenance"].startswith("KMA(")

    asyncio.run(_run())


def test_npms_fetcher_returns_bulletins() -> None:
    async def _run() -> None:
        fetcher = NpmsFetcher(api_key="dummy-key")

        npms_payload = {
            "service": {
                "pestModelByKncrList": [
                    {
                        "kncrCode": "FC010101",
                        "dbyhsMdlNm": "Rice%20Blast",
                        "validAlarmRiskIdex": "2",
                        "pestConfigStr": "Warning!+@+!Action%20needed!+@+!FF3C00|Notice!+@+!Monitor!+@+!001AFF",
                        "nowDrveDatetm": "2025100412",
                    },
                    {
                        "kncrCode": "VC011205",
                        "dbyhsMdlNm": "Pepper%20Blight",
                        "validAlarmRiskIdex": "1",
                        "pestConfigStr": "Alert!+@+!Severe!+@+!FF0000",
                        "nowDrveDatetm": "2025100412",
                    },
                ]
            }
        }

        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=npms_payload)

        fetcher._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))  # noqa: SLF001 - testing internal override
        result = await fetcher.fetch(_resolved_profile("rice"))
        await fetcher.aclose()

        assert result is not None
        assert result["bulletins"], "Expected at least one bulletin"
        first = result["bulletins"][0]
        assert first["pest"] == "Rice Blast"
        assert first["risk"] == "HIGH"
        assert first["summary"].startswith("Notice")
        assert first["since"] == "2025-10-04"

    asyncio.run(_run())
