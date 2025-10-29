"""HTTP fetchers for external climate and pest data sources."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from cachetools import TTLCache

from src.services.aggregation.models import ResolvedProfile


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
    """Short-range forecast + warnings from KMA APIs."""

    def __init__(self) -> None:
        super().__init__(ttl_seconds=60 * 60, maxsize=16)

    async def fetch(self, resolved: ResolvedProfile) -> dict | None:
        key = self._cache_key(resolved)
        if key in self._cache:
            return self._cache[key]

        raise NotImplementedError("Live KMA fetch integration pending.")


class OpenMeteoFetcher(BaseFetcher):
    """Open-Meteo hourly/daily forecast (fallback + extended horizon)."""

    def __init__(self) -> None:
        super().__init__(ttl_seconds=3 * 60 * 60, maxsize=32)

    async def fetch(self, resolved: ResolvedProfile) -> dict | None:
        key = self._cache_key(resolved)
        if key in self._cache:
            return self._cache[key]

        raise NotImplementedError("Live Open-Meteo fetch integration pending.")


class NpmsFetcher(BaseFetcher):
    """NPMS crop/region pest warnings."""

    def __init__(self) -> None:
        super().__init__(ttl_seconds=12 * 60 * 60, maxsize=16)

    async def fetch(self, resolved: ResolvedProfile) -> dict | None:
        key = self._cache_key(resolved)
        if key in self._cache:
            return self._cache[key]

        raise NotImplementedError("Live NPMS fetch integration pending.")


__all__ = ["KmaFetcher", "OpenMeteoFetcher", "NpmsFetcher"]
