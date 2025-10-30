# Implementation Plan: API Aggregation — Andong Apple

**Branch**: `002-api-aggregation` | **Date**: 2025-10-30 | **Spec**: specs/002-API-Aggregation/spec.md
**Input**: Narrowed scope to Andong‑si apple MVP

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Monolithic FastAPI aggregator for a single scenario: Andong‑si apple orchards.
Accept `region,crop,stage`, resolve Andong IDs, fetch KMA mid‑term summaries,
Open‑Meteo numeric daily/hourly, and NPMS apple bulletins **plus Andong 예찰
observations (SVC51→SVC53)**. Perform minimal
normalization (KST timestamps, units, unified keys), compute optional
deterministic soft hints, and return one Evidence Pack for the LLM.

Scope: D0–D10 (daily) and ≤72h (hourly); crop = `apple` only; region = `Andong-si` only.
Preserve provenance; no averaging/bias correction. If KMA or NPMS are unavailable,
continue with available sources and explicit provenance.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI; httpx (async, timeouts/retries) or urllib; pydantic v2; cachetools (TTLCache); `zoneinfo` (KST); uvicorn  
**Storage**: None (in‑memory TTL caches only)  
**Testing**: pytest; httpx.MockTransport for parser units; contract tests for `/api/aggregate`  
**Target Platform**: Single server (monolith; serves API only)  
**Performance Goals**: p95 < 2s cold; warm cache < 300ms  
**Constraints**: Minimal normalization only; no hard triggers; preserve raw arrays; deterministic optional soft hints  
**Scale/Scope**: Single profile (Andong‑apple) for MVP

Implementation notes:
- Resolver: preload `("andong-si","apple")` → `{ lat: 36.568, lon: 128.729, kma_area_code: "11H10501" }`.
- Fetchers: parallelize KMA (MidFcstInfoService summaries), Open‑Meteo (numeric),
  NPMS SVC31 (apple risk bulletins) **and SVC51→SVC53 (Andong observation metrics)**
  with httpx/urllib; timeouts + TTL cache.
- Normalization: keys/units unified; timestamps → ISO8601 +09:00; daily `date` = `YYYY-MM-DD`.
- Merge policy: numeric = Open‑Meteo primary; KMA `summary/precip_probability_pct` attached alongside numeric; warnings from KMA when available.
- Soft hints: deterministic calculations (rain runs, heat/wind hours, wet nights, diurnal range, first warning type) — advisory only.
- Caching: TTL per-source (KMA 1–3h; Open‑Meteo ~3h; NPMS 12–24h). Cache key uses `{crop,lat,lon}`.
- Fallbacks: missing KMA → numeric only; missing NPMS → `bulletins: []`; provenance explicit.
- Logging: `req_id, region, crop, fetched:{kma,om,npms}, duration_ms` (JSON line).
- Demo switch: `?demo=true` scripted Andong‑apple scenario.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Single MVP: PASS — one aggregator endpoint producing one Evidence Pack.
- Channel: PASS — backend only, supporting the single SMS+link channel.
- Simplicity: PASS — monolith, minimal normalization, no extra analytics stack.
- Integrations: EXCEPTION — three external sources (KMA, Open‑Meteo, NPMS); mitigated via TTL cache and demo switch. Single profile reduces risk.

## Phases & Tasks

1) Scope alignment (completed)
- Narrow spec to Andong‑si apple; define resolver defaults and KMA/NPMS codes.

2) Data model adjustments
- Extend `ClimateDaily` with optional `summary`, `precip_probability_pct` to carry KMA mid‑term fields.

3) Resolver + fetchers
- Add `("andong-si","apple")` record to resolver.
- NPMS: ensure apple code `FT010601` is supported; parse and map risk indices to LOW/MODERATE/HIGH/ALERT; **resolve SVC51 insectKey (fallback to
  202500209FT01060101322008), map SVC53 안동 observations, and surface deterministic pest hints (복숭아순나방 트랩 ≥10).**

4) Merge policy + soft hints
- Implement Open‑Meteo primary numeric with KMA summary overlay; keep provenance; compute soft hints.

5) Endpoint + tests
- Contract test for `/api/aggregate` with `Andong-si/apple` demo payload; parser unit tests for KMA summary and NPMS apple samples.

6) Ops & docs
- Update `.env.sample` for `KMA_API_KEY`, `NPMS_API_KEY`; add runbook snippets for `scripts/api_probe.py`.
- Ship-to-learn: PASS — fast iteration via in‑memory cache and scripted demos.
