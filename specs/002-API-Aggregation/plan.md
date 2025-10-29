# Implementation Plan: API Aggregation — Raw + Soft Hints

**Branch**: `002-api-aggregation` | **Date**: 2025-10-29 | **Spec**: /home/tomto/projects/farm-climate-reporter/specs/002-API-Aggregation/spec.md
**Input**: Feature specification from `/specs/002-API-Aggregation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a monolithic FastAPI aggregator that accepts a simple farm profile
(`region,crop,stage`), resolves location IDs, fetches KMA (short-range + warnings),
Open‑Meteo (daily/hourly), and NPMS (crop/region bulletins), performs minimal
normalization (KST timestamps, units, unified keys), optionally computes deterministic
non-binding soft hints, and returns a single Evidence Pack for the LLM.

Scope: Horizon D0–D10 (daily) and ≤72h (hourly); crops limited to rice/lettuce/tomato.
Preserve provenance; keep arrays as-is; no averaging or bias correction. Fallback to
Open‑Meteo if KMA is unavailable; NPMS absence yields empty bulletins.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI; httpx (async, timeouts/retries); pydantic v2; cachetools (TTLCache); standard `zoneinfo` for `Asia/Seoul`; uvicorn  
**Storage**: None (in‑memory TTL caches only)  
**Testing**: pytest; respx (httpx mocking); contract tests for `/api/aggregate`  
**Target Platform**: Single server (monolith; serves API only)  
**Project Type**: single  
**Performance Goals**: p95 < 2s for cold fetch; warm cache < 300ms  
**Constraints**: Minimal normalization only; no hard triggers; preserve raw arrays; Korean KST timestamps; deterministic optional soft hints  
**Scale/Scope**: Demo‑scale (≤10 demo profiles; light traffic)

Implementation notes:
- Resolver: map `region` → `{lat,lon}`, `kma_grid` (e.g., `{nx,ny}` or area code), and `npms_region_code`. For hackathon, preload demo profiles with all IDs.
- Fetchers: parallelize KMA, Open‑Meteo, NPMS with httpx.AsyncClient; strict timeouts; small retry policy.
- Normalization: unify keys/units: `°C`, `mm`, `m/s`, `%`; timestamps → ISO8601 +09:00; keep daily `date` as `YYYY-MM-DD`.
- Merge policy: D0–D3 prefer KMA, D4–D10 prefer Open‑Meteo; warnings always KMA; annotate optional `daily[i].src` when filled.
- Soft hints (optional): deterministic computations from normalized data; never override raw/warnings.
- Caching: TTL per-source (KMA 1–3h; Open‑Meteo ~3h; NPMS 12–24h). Cache keyed by resolved IDs and horizon.
- Fallbacks: KMA down → use Open‑Meteo only; NPMS empty → `bulletins: []`; always keep `provenance`.
- Logging: minimal JSON line with `req_id, region, crop, fetched:{kma,om,npms}, cache_hit, duration_ms`.
- Demo switch: `?demo=true` serves scripted scenarios for predictable outputs.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Single MVP: PASS — one aggregator endpoint producing one Evidence Pack.
- Channel: PASS — backend only, supporting the single SMS+link channel.
- Simplicity: PASS — monolith, minimal normalization, no extra analytics stack.
- Integrations: EXCEPTION — three external sources (KMA, Open‑Meteo, NPMS); required by spec; mitigated via TTL cache and demo switch.
- Ship-to-learn: PASS — fast iteration via in‑memory cache and scripted demos.
