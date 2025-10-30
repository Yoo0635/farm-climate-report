"""HTTP fetchers for external climate and pest data sources."""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import date, datetime, time, timedelta
from html import unescape
from typing import Any, Iterable
from urllib.parse import unquote
from zoneinfo import ZoneInfo

import httpx
from cachetools import TTLCache

from src.services.aggregation.models import ResolvedProfile

logger = logging.getLogger(__name__)
KST = ZoneInfo("Asia/Seoul")


class BaseFetcher:
    """Shared utilities for cached HTTP fetchers."""

    def __init__(self, ttl_seconds: int, maxsize: int = 32) -> None:
        self._cache: TTLCache[str, Any] = TTLCache(maxsize=maxsize, ttl=ttl_seconds)
        self._client: httpx.AsyncClient | None = None
        self._lock = asyncio.Lock()

    async def _get_client(self) -> httpx.AsyncClient:
        async with self._lock:
            if self._client is None:
                self._client = httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0, read=10.0))
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    def _cache_key(self, resolved: ResolvedProfile) -> str:
        crop = resolved.profile.crop
        lat = f"{resolved.lat:.3f}"
        lon = f"{resolved.lon:.3f}"
        return f"{crop}:{lat}:{lon}"


class KmaFetcher(BaseFetcher):
    """Mid-term land forecast + (stubbed) warnings from KMA API Hub."""

    def __init__(self, auth_key: str | None = None) -> None:
        super().__init__(ttl_seconds=60 * 60, maxsize=16)
        self._auth_key = auth_key or _env_first("KMA_API_KEY", "KMA_AUTH_KEY", "KMA_SERVICE_KEY")
        self._base_url = os.environ.get("KMA_API_BASE_URL", "https://apihub.kma.go.kr/api/typ02/openApi")

    async def fetch(self, resolved: ResolvedProfile) -> dict | None:
        key = self._cache_key(resolved)
        if key in self._cache:
            return self._cache[key]

        auth_key = self._auth_key or _env_first("KMA_API_KEY", "KMA_AUTH_KEY", "KMA_SERVICE_KEY")
        if not auth_key:
            logger.warning("KMA fetch skipped — API key not configured")
            return None
        if not resolved.kma_area_code:
            logger.warning("KMA fetch skipped — profile lacks kma_area_code (region=%s crop=%s)", resolved.profile.region, resolved.profile.crop)
            return None

        client = await self._get_client()
        endpoint = f"{self._base_url}/MidFcstInfoService/getMidLandFcst"
        for tmfc_dt in self._candidate_tmfc():
            params = {
                "authKey": auth_key,
                "dataType": "JSON",
                "pageNo": "1",
                "numOfRows": "50",
                "regId": resolved.kma_area_code,
                "tmFc": tmfc_dt.strftime("%Y%m%d%H%M"),
            }
            try:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                logger.warning("KMA MidFcst request failed (tmFc=%s, area=%s): %s", params["tmFc"], resolved.kma_area_code, exc)
                continue

            try:
                payload = response.json()
            except ValueError as exc:  # pragma: no cover - defensive guard
                logger.warning("KMA MidFcst returned non-JSON payload (tmFc=%s): %s", params["tmFc"], exc)
                continue

            parsed = self._parse_mid_land(payload, tmfc_dt, resolved.kma_area_code)
            if parsed is None:
                continue

            parsed["provenance"] = parsed.get("provenance") or f"KMA({tmfc_dt.date().isoformat()})"
            self._cache[key] = parsed
            return parsed

        logger.warning("KMA MidFcst yielded no usable data for area %s", resolved.kma_area_code)
        return None

    def _candidate_tmfc(self) -> list[datetime]:
        """Return candidate publication timestamps (latest first)."""
        now = datetime.now(tz=KST)
        candidates: set[datetime] = set()
        for day_offset in range(0, 3):
            day = now.date() - timedelta(days=day_offset)
            for hour in (18, 6):
                candidate = datetime.combine(day, time(hour=hour), tzinfo=KST)
                # Allow slight look-ahead in case of just-published bulletins.
                if candidate <= now + timedelta(hours=1):
                    candidates.add(candidate)
        return sorted(candidates, reverse=True)

    def _parse_mid_land(self, payload: dict[str, Any], tmfc_dt: datetime, reg_id: str) -> dict | None:
        """Extract daily summaries from KMA MidFcstInfoService response."""
        response = payload.get("response")
        if not isinstance(response, dict):
            return None
        header = response.get("header") or {}
        if header.get("resultCode") != "00":
            logger.info("KMA MidFcst returned resultCode=%s message=%s", header.get("resultCode"), header.get("resultMsg"))
            return None

        body = response.get("body") or {}
        items = body.get("items")
        records: Iterable[dict[str, Any]] = ()
        if isinstance(items, dict):
            item = items.get("item")
            if isinstance(item, list):
                records = item
            elif isinstance(item, dict):
                records = [item]
        elif isinstance(items, list):
            records = items

        target: dict[str, Any] | None = None
        for record in records or []:
            if str(record.get("regId")) == str(reg_id):
                target = record
                break
        if target is None and records:
            target = next(iter(records))
        if target is None:
            return None

        daily: list[dict[str, Any]] = []
        for day in range(4, 8):
            entry = self._build_mid_land_day(target, tmfc_dt, day, am_pm=True)
            if entry:
                daily.append(entry)
        for day in range(8, 11):
            entry = self._build_mid_land_day(target, tmfc_dt, day, am_pm=False)
            if entry:
                daily.append(entry)

        return {
            "issued_at": tmfc_dt.isoformat(),
            "daily": daily,
            "hourly": [],
            "warnings": [],
        }

    def _build_mid_land_day(self, data: dict[str, Any], tmfc_dt: datetime, day: int, *, am_pm: bool) -> dict[str, Any] | None:
        summary_parts: list[str] = []
        chance_values: list[float] = []

        if am_pm:
            for suffix in ("Am", "Pm"):
                wf = _clean_text(data.get(f"wf{day}{suffix}"))
                rn = _to_float(data.get(f"rnSt{day}{suffix}"))
                if wf:
                    summary_parts.append(wf)
                if rn is not None:
                    chance_values.append(rn)
        else:
            wf = _clean_text(data.get(f"wf{day}"))
            rn = _to_float(data.get(f"rnSt{day}"))
            if wf:
                summary_parts.append(wf)
            if rn is not None:
                chance_values.append(rn)

        if not summary_parts and not chance_values:
            return None

        forecast_date = (tmfc_dt + timedelta(days=max(day - 1, 0))).date().isoformat()
        entry: dict[str, Any] = {
            "date": forecast_date,
            "precip_mm": None,  # Mid-term feed provides probability only; leave numeric fields empty.
        }
        if summary_parts:
            entry["summary"] = " / ".join(summary_parts)
        if chance_values:
            entry["precip_probability_pct"] = round(sum(chance_values) / len(chance_values), 1)
        return entry


class OpenMeteoFetcher(BaseFetcher):
    """Open-Meteo hourly/daily forecast (fallback + extended horizon)."""

    def __init__(self, base_url: str | None = None) -> None:
        super().__init__(ttl_seconds=3 * 60 * 60, maxsize=32)
        self._base_url = base_url or os.environ.get("OPEN_METEO_BASE_URL", "https://api.open-meteo.com/v1/forecast")

    async def fetch(self, resolved: ResolvedProfile) -> dict | None:
        key = self._cache_key(resolved)
        if key in self._cache:
            return self._cache[key]

        params = {
            "latitude": resolved.lat,
            "longitude": resolved.lon,
            "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_gusts_10m,precipitation,shortwave_radiation",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max",
            "forecast_days": "10",
            "timezone": "Asia/Seoul",
        }

        client = await self._get_client()
        try:
            response = await client.get(self._base_url, params=params)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Open-Meteo request failed (lat=%.3f lon=%.3f): %s", resolved.lat, resolved.lon, exc)
            return None

        try:
            payload = response.json()
        except ValueError as exc:  # pragma: no cover - defensive
            logger.warning("Open-Meteo returned non-JSON payload: %s", exc)
            return None

        parsed = self._parse_open_meteo(payload)
        if parsed is None:
            return None

        self._cache[key] = parsed
        return parsed

    def _parse_open_meteo(self, payload: dict[str, Any]) -> dict | None:
        daily_block = payload.get("daily") or {}
        hourly_block = payload.get("hourly") or {}

        daily_times = daily_block.get("time") or []
        if not isinstance(daily_times, list) or not daily_times:
            return None

        daily_entries: list[dict[str, Any]] = []
        for idx, day_str in enumerate(daily_times):
            try:
                day_date = datetime.fromisoformat(day_str).date()
            except ValueError:
                continue
            tmax = _to_float(_safe_get(daily_block, "temperature_2m_max", idx))
            tmin = _to_float(_safe_get(daily_block, "temperature_2m_min", idx))
            precip = _to_float(_safe_get(daily_block, "precipitation_sum", idx))
            wind_kmh = _to_float(_safe_get(daily_block, "windspeed_10m_max", idx))
            wind_ms = wind_kmh / 3.6 if wind_kmh is not None else None
            daily_entries.append(
                {
                    "date": day_date.isoformat(),
                    "tmax_c": tmax,
                    "tmin_c": tmin,
                    "precip_mm": precip,
                    "wind_ms": wind_ms,
                }
            )

        hourly_times = hourly_block.get("time") or []
        if not isinstance(hourly_times, list) or not hourly_times:
            return None

        hourly_entries: list[dict[str, Any]] = []
        for idx, ts_str in enumerate(hourly_times):
            if idx >= 72:
                break
            try:
                ts = datetime.fromisoformat(ts_str).replace(tzinfo=KST)
            except ValueError:
                continue

            temp = _to_float(_safe_get(hourly_block, "temperature_2m", idx))
            rh = _to_float(_safe_get(hourly_block, "relative_humidity_2m", idx))
            wind_kmh = _to_float(_safe_get(hourly_block, "wind_speed_10m", idx))
            gust_kmh = _to_float(_safe_get(hourly_block, "wind_gusts_10m", idx))
            precip = _to_float(_safe_get(hourly_block, "precipitation", idx))
            swrad = _to_float(_safe_get(hourly_block, "shortwave_radiation", idx))

            hourly_entries.append(
                {
                    "ts": ts.isoformat(),
                    "t_c": temp,
                    "rh_pct": rh,
                    "wind_ms": wind_kmh / 3.6 if wind_kmh is not None else None,
                    "gust_ms": gust_kmh / 3.6 if gust_kmh is not None else None,
                    "precip_mm": precip,
                    "swrad_wm2": swrad,
                }
            )

        issued_at = datetime.now(tz=KST)
        return {
            "issued_at": issued_at.isoformat(),
            "daily": daily_entries,
            "hourly": hourly_entries,
            "provenance": f"Open-Meteo({issued_at.date().isoformat()})",
        }


class NpmsFetcher(BaseFetcher):
    """NPMS crop/region pest warnings."""

    _CROP_CODE_MAP = {
        "apple": "FT010601",  # 사과
    }

    _RISK_ORDER = {"ALERT": 0, "HIGH": 1, "MODERATE": 2, "LOW": 3}

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(ttl_seconds=12 * 60 * 60, maxsize=16)
        self._api_key = api_key or os.environ.get("NPMS_API_KEY")
        self._base_url = os.environ.get("NPMS_API_BASE_URL", "http://ncpms.rda.go.kr/npmsAPI/service")
        self._predict_code = os.environ.get("NPMS_DEFAULT_PREDICT_CODE", "00209")
        self._svc51_type = os.environ.get("NPMS_SVC51_TYPE", "AA003")
        self._svc53_type = os.environ.get("NPMS_SVC53_TYPE", "AA003")
        self._default_insect_key = os.environ.get("NPMS_DEFAULT_INSECT_KEY", "202500209FT01060101322008")

    async def fetch(self, resolved: ResolvedProfile) -> dict | None:
        key = self._cache_key(resolved)
        if key in self._cache:
            return self._cache[key]

        api_key = self._api_key or os.environ.get("NPMS_API_KEY")
        if not api_key:
            logger.info("NPMS fetch skipped — API key not configured")
            return None

        crop_code = self._CROP_CODE_MAP.get(resolved.profile.crop)
        if not crop_code:
            logger.info("NPMS fetch skipped — crop not supported (crop=%s)", resolved.profile.crop)
            return None

        client = await self._get_client()
        bulletins = await self._fetch_bulletins(client, api_key, resolved.profile.crop, crop_code)
        observations = await self._fetch_observations(client, api_key, resolved, crop_code)

        if not bulletins and not observations:
            return None

        issued_at = None
        provenance: list[str] = []
        payload: dict[str, Any] = {
            "crop": resolved.profile.crop,
            "bulletins": [],
            "observations": [],
        }

        if bulletins:
            issued_at = bulletins.get("issued_at")
            payload["bulletins"] = bulletins.get("bulletins", [])
            _merge_provenance(provenance, bulletins.get("provenance"))

        if observations:
            issued_at = issued_at or observations.get("issued_at")
            payload["observations"] = observations.get("observations", [])
            _merge_provenance(provenance, observations.get("provenance"))

        if issued_at is None:
            issued_at = datetime.now(tz=KST).isoformat()

        payload["issued_at"] = issued_at
        if provenance:
            payload["provenance"] = provenance

        self._cache[key] = payload
        return payload

    async def _fetch_bulletins(
        self,
        client: httpx.AsyncClient,
        api_key: str,
        crop: str,
        crop_code: str,
    ) -> dict[str, Any] | None:
        params = {
            "apiKey": api_key,
            "serviceCode": "SVC31",
            "proxyUrl": "https://example.com/callback",
            "div_id": "result",
            "cropList": crop_code,
        }

        payload = await self._request_json(client, params)
        if payload is None:
            return None

        return self._parse_npms_bulletins(payload, crop, crop_code)

    async def _fetch_observations(
        self,
        client: httpx.AsyncClient,
        api_key: str,
        resolved: ResolvedProfile,
        crop_code: str,
    ) -> dict[str, Any] | None:
        if not resolved.npms_region_code:
            return None

        insect_key = await self._lookup_insect_key(client, api_key, crop_code)
        if not insect_key:
            return None

        params = {
            "apiKey": api_key,
            "serviceCode": "SVC53",
            "serviceType": self._svc53_type,
            "insectKey": insect_key,
            "sidoCode": _derive_sido_code(resolved.npms_region_code),
        }

        payload = await self._request_json(client, params)
        if payload is None:
            return None

        return self._parse_npms_observations(payload, resolved.npms_region_code)

    async def _lookup_insect_key(
        self,
        client: httpx.AsyncClient,
        api_key: str,
        crop_code: str,
    ) -> str | None:
        payload = await self._request_json(client, params)
        if payload:
            service = payload.get("service") or {}
            entries = service.get("list") or []
            if isinstance(entries, dict):
                entries = [entries]
            if entries:
                filtered = []
                for entry in entries:
                    if self._predict_code and entry.get("predictnSpchcknCode") != self._predict_code:
                        continue
                    filtered.append(entry)

                candidates = filtered or entries
                candidates.sort(key=_svc51_sort_key, reverse=True)
                for entry in candidates:
                    insect_key = entry.get("insectKey")
                    if insect_key:
                        return insect_key

        if self._default_insect_key:
            logger.debug("NPMS SVC51 lookup failed; falling back to default insectKey %s", self._default_insect_key)
            return self._default_insect_key
        return None

    async def _request_json(self, client: httpx.AsyncClient, params: dict[str, str]) -> dict[str, Any] | None:
        try:
            response = await client.get(self._base_url, params=params)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("NPMS request failed (serviceCode=%s): %s", params.get("serviceCode"), exc)
            return None

        try:
            return response.json()
        except ValueError as exc:  # pragma: no cover - defensive
            logger.warning("NPMS returned non-JSON payload: %s", exc)
            return None

    def _parse_npms_bulletins(self, payload: dict[str, Any], crop: str, crop_code: str) -> dict[str, Any] | None:
        service = payload.get("service") or {}
        models = service.get("pestModelByKncrList") or []
        if isinstance(models, dict):
            models = [models]
        if not models:
            return None

        bulletins: list[dict[str, Any]] = []
        seen_pests: set[str] = set()

        for raw_entry in models:
            entry = {_clean_text(k): _clean_text(unquote(str(v))) for k, v in raw_entry.items()}
            if entry.get("kncrCode") != crop_code:
                continue

            pest_name = entry.get("dbyhsMdlNm")
            if not pest_name or pest_name in seen_pests:
                continue

            risk_index = _to_int(entry.get("validAlarmRiskIdex"), default=1)
            segments = _parse_npms_segments(entry.get("pestConfigStr", ""))
            summary, color = _select_npms_segment(segments, risk_index)
            risk = _npms_risk_from_index(risk_index, color)
            since = _parse_npms_datetime(entry.get("nowDrveDatetm"))

            bulletins.append(
                {
                    "pest": pest_name,
                    "risk": risk,
                    "since": since or date.today().isoformat(),
                    "summary": summary or f"{pest_name} 관련 경보가 발효 중입니다.",
                }
            )
            seen_pests.add(pest_name)

        bulletins.sort(key=lambda entry: self._RISK_ORDER.get(entry["risk"], 99))
        issued_at = datetime.now(tz=KST)
        return {
            "issued_at": issued_at.isoformat(),
            "crop": crop,
            "bulletins": bulletins[:5],
            "provenance": f"NPMS-SVC31({issued_at.date().isoformat()})",
        }

    def _parse_npms_observations(self, payload: dict[str, Any], region_code: str) -> dict[str, Any] | None:
        service = payload.get("service") or {}
        entries = service.get("structList") or []
        if isinstance(entries, dict):
            entries = [entries]
        if not entries:
            return None

        targets = _region_code_variants(region_code)
        observations: list[dict[str, Any]] = []
        for entry in entries:
            sigungu_code = str(entry.get("sigunguCode") or "").strip()
            if sigungu_code not in targets:
                continue

            name = _clean_text(entry.get("dbyhsNm"))
            pest, metric, unit = _split_metric_name(name)

            observations.append(
                {
                    "pest": pest,
                    "metric": metric,
                    "unit": unit,
                    "code": _clean_text(entry.get("inqireCnClCode")),
                    "value": _to_float(entry.get("inqireValue")),
                    "area": _clean_text(entry.get("sigunguNm")),
                }
            )

        if not observations:
            return None

        issued_at = datetime.now(tz=KST)
        return {
            "issued_at": issued_at.isoformat(),
            "observations": observations,
            "provenance": f"NPMS-SVC53({issued_at.date().isoformat()})",
        }


def _env_first(*keys: str) -> str | None:
    for key in keys:
        value = os.environ.get(key)
        if value:
            return value
    return None


def _to_float(value: Any) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _clean_text(value: Any) -> str:
    if value in (None, "", "-"):
        return ""
    if isinstance(value, str):
        unescaped = unescape(value.replace("&nbsp", " ").replace("\xa0", " "))
        return " ".join(unescaped.split())
    return str(value)


def _safe_get(container: dict[str, Any], key: str, idx: int) -> Any:
    values = container.get(key)
    if not isinstance(values, list):
        return None
    if idx >= len(values):
        return None
    return values[idx]


def _parse_npms_segments(config: str) -> list[tuple[str, str, str]]:
    segments: list[tuple[str, str, str]] = []
    for raw_segment in config.split("|"):
        parts = raw_segment.split("!+@+!")
        if len(parts) != 3:
            continue
        title = _clean_text(parts[0])
        body = _clean_text(parts[1])
        color = parts[2].strip().upper()
        if not title and not body:
            continue
        segments.append((title, body, color))
    return segments


def _select_npms_segment(segments: list[tuple[str, str, str]], index: int) -> tuple[str | None, str | None]:
    if not segments:
        return None, None
    clamped = max(1, min(index, len(segments)))
    title, body, color = segments[clamped - 1]
    combined = " ".join(part for part in (title, body) if part).strip() or None
    return combined, color


def _npms_risk_from_index(index: int, color: str | None) -> str:
    if index <= 1:
        return "ALERT"
    if index == 2:
        return "HIGH"
    if index == 3:
        return "MODERATE"
    return "LOW"


def _parse_npms_datetime(value: str | None) -> str | None:
    if not value:
        return None
    for fmt in ("%Y%m%d%H%M", "%Y%m%d%H"):
        try:
            dt = datetime.strptime(value, fmt).replace(tzinfo=KST)
            return dt.date().isoformat()
        except ValueError:
            continue
    return None


def _merge_provenance(container: list[str], value: Any) -> None:
    if not value:
        return
    if isinstance(value, str):
        container.append(value)
    elif isinstance(value, list):
        for item in value:
            if item:
                container.append(str(item))


def _svc51_sort_key(entry: dict[str, Any]) -> tuple[int, int]:
    raw_date = str(entry.get("inputStdrDatetm") or "")
    try:
        date_val = int(raw_date)
    except ValueError:
        date_val = 0
    tmrd = _to_int(entry.get("examinTmrd"), default=0)
    return date_val, tmrd


def _derive_sido_code(region_code: str) -> str:
    text = str(region_code).strip()
    if len(text) >= 2:
        return text[:2]
    return text


def _region_code_variants(region_code: str) -> set[str]:
    text = str(region_code).strip()
    variants = {
        text,
        text.rstrip("0"),
        text.lstrip("0"),
        text[:4],
        text[:5],
    }
    return {variant for variant in variants if variant}


def _split_metric_name(name: str) -> tuple[str, str, str | None]:
    cleaned = _clean_text(name)
    if "(" in cleaned and cleaned.endswith(")"):
        pest, rest = cleaned.split("(", 1)
        metric = rest.rstrip(")")
        return pest.strip(), metric.strip(), None
    return cleaned, "", None


__all__ = ["KmaFetcher", "OpenMeteoFetcher", "NpmsFetcher"]
