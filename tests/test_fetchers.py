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


def _resolved_profile() -> ResolvedProfile:
    profile = AggregateProfile(region="Andong-si", crop="apple", stage="flowering")
    return ResolvedProfile(
        profile=profile,
        lat=36.568,
        lon=128.729,
        kma_grid=None,
        kma_area_code="11H10501",
        npms_region_code="47170",
    )


def test_open_meteo_fetcher_parses_payload() -> None:
    async def _run() -> None:
        fetcher = OpenMeteoFetcher()

        start = datetime(2025, 10, 30, 0, 0)
        hours = [
            (start + timedelta(hours=hour)).strftime("%Y-%m-%dT%H:%M")
            for hour in range(75)
        ]
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
            return httpx.Response(
                200, json={"daily": daily_payload, "hourly": hourly_payload}
            )

        fetcher._client = httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        )  # noqa: SLF001 - testing internal override
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
                                "regId": "11H10501",
                                "wf4Am": "맑음",
                                "wf4Pm": "구름많음",
                                "rnSt4Am": 10,
                                "rnSt4Pm": 20,
                                "wf5Am": "구름많음",
                                "wf5Pm": "흐림",
                                "rnSt5Am": 40,
                                "rnSt5Pm": 60,
                                "wf8": "비",
                                "rnSt8": 50,
                                "rnSt9": 20,
                                "wf9": "맑음",
                            }
                        ]
                    }
                },
            }
        }

        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=mid_payload)

        fetcher._client = httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        )  # noqa: SLF001 - testing internal override
        result = await fetcher.fetch(_resolved_profile())
        await fetcher.aclose()

        assert result is not None
        assert result["daily"][0]["date"] == "2025-11-01"
        assert result["daily"][0]["summary"]
        assert result["daily"][0]["precip_probability_pct"] == 15.0
        assert result["provenance"].startswith("KMA(")

    asyncio.run(_run())


def test_npms_fetcher_returns_bulletins() -> None:
    async def _run() -> None:
        fetcher = NpmsFetcher(api_key="dummy-key")

        svc31_payload = {
            "service": {
                "pestModelByKncrList": [
                    {
                        "kncrCode": "FT010601",
                        "dbyhsMdlNm": "%EA%B0%88%EC%83%89%EB%AC%B4%EB%8A%AC%EB%B3%91",
                        "validAlarmRiskIdex": "2",
                        "pestConfigStr": "2%EB%8B%A8%EA%B3%84!+@+!%EB%B0%9C%EC%83%9D%20%EC%A6%9D%EA%B0%80%20%EA%B3%A1%EB%8B%A8%20%EA%B4%80%EB%A6%AC!+@+!FF3C00|1%EB%8B%A8%EA%B3%84!+@+!%ED%99%94%EB%B6%84%20%EC%A3%BC%EC%9D%98!+@+!001AFF",
                        "nowDrveDatetm": "2025100412",
                    },
                ]
            }
        }

        svc51_payload = {
            "service": {
                "list": [
                    {
                        "predictnSpchcknCode": "00209",
                        "insectKey": "202500209FT01060101322008",
                        "examinTmrd": "8",
                        "inputStdrDatetm": "20250901",
                    }
                ]
            }
        }

        svc53_payload = {
            "service": {
                "structList": [
                    {
                        "dbyhsNm": "사과굴나방(트랩당마리수)",
                        "inqireCnClCode": "SS0128",
                        "inqireValue": "12.4",
                        "sigunguNm": "안동시",
                        "sigunguCode": "4717",
                    },
                    {
                        "dbyhsNm": "사과굴나방(트랩당마리수)",
                        "inqireCnClCode": "SS0128",
                        "inqireValue": "99.9",
                        "sigunguNm": "상주시",
                        "sigunguCode": "4725",
                    },
                ]
            }
        }

        def handler(request: httpx.Request) -> httpx.Response:
            service_code = request.url.params.get("serviceCode")
            if service_code == "SVC31":
                return httpx.Response(200, json=svc31_payload)
            if service_code == "SVC51":
                return httpx.Response(200, json=svc51_payload)
            if service_code == "SVC53":
                return httpx.Response(200, json=svc53_payload)
            return httpx.Response(404, json={"error": "unexpected serviceCode"})

        fetcher._client = httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        )  # noqa: SLF001 - testing internal override
        result = await fetcher.fetch(_resolved_profile())
        await fetcher.aclose()

        assert result is not None
        assert result["bulletins"], "Expected at least one bulletin"
        first = result["bulletins"][0]
        assert first["pest"] == "갈색무늬병"
        assert first["risk"] == "HIGH"
        assert "발생" in first["summary"]
        assert first["since"] == "2025-10-04"
        assert result["observations"], "Expected observation records"
        obs = result["observations"][0]
        assert obs["pest"] == "사과굴나방"
        assert obs["metric"] == "트랩당마리수"
        assert obs["area"] == "안동시"
        assert obs["value"] == pytest.approx(12.4)
        assert len(result.get("provenance", [])) >= 2

    asyncio.run(_run())
