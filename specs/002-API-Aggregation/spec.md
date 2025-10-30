# API Aggregation Spec — Andong Apple (KMA · NPMS · Open‑Meteo)

> Purpose: Backend fetches three sources, does **minimal normalization**, computes **non-binding soft hints**, and hands a single **evidence pack** to the LLM.
> Scope (MVP narrowed): **Andong‑si apple orchards only**; horizon **D0–D10**; monolithic FastAPI service.
> **IMPORTANT: This specification is a draft and is subject to change at any time. If there is a reasonable justification, you should plan outside the specification and then modify this document.**
---

## 0) Principles

* **No hard triggers.** The LLM reasons primarily from raw data.
* **Minimal normalize only**: time zone, units, and key names. No bias-correction/regridding.
* **Soft hints are advisory**; if they conflict with raw/warnings, the model must prefer raw.

---

## 1) Inputs & Identity (Andong Apple Only)

**Request (Profile)**

```json
{"region":"Andong-si","crop":"apple","stage":"flowering"}
```

**Resolver (derived once, Andong defaults)**

- `lat, lon`: 36.568, 128.729 (Andong‑si center; used by Open‑Meteo)
- `kma_area_code`: `11H10501` (KMA 중기예보 지역코드 — 안동)
- `kma_grid`: optional for short‑range; not required for this MVP
- `npms_crop_code`: `FT010601` (사과)

For MVP, preload a single resolver record for `("andong-si", "apple")`.

---

## 2) External Fetchers & Fields to Keep

### A) **KMA** (mid‑term summaries + future warnings)

Keep:

```json
{
  "issued_at": "ISO8601+09:00",
  "daily": [ {"date":"YYYY-MM-DD","summary":"맑음 / 구름많음","precip_probability_pct":10.0} ],
  "hourly": [],
  "warnings": [ ... ]  // optional; may be unavailable initially
  "provenance": "KMA(YYYY-MM-DD)"
}
```

### B) **Open‑Meteo** (primary numeric daily + hourly; fallback)

Keep (same keys/units as KMA):

```json
{
  "issued_at": "ISO8601",
  "daily": [ {"date":"YYYY-MM-DD","tmax_c":32.0,"tmin_c":23.0,"precip_mm":5.0,"wind_ms":6.0} ],
  "hourly":[ {"ts":"ISO8601","t_c":30.2,"rh_pct":60,"wind_ms":4.8,"gust_ms":7.5,"precip_mm":0.0,"swrad_wm2":650} ],
  "provenance": "Open-Meteo(YYYY-MM-DD)"
}
```

### C) **NPMS** (apple pest bulletins)

Keep (decision-driving only):

```json
{
  "issued_at":"ISO8601+09:00",
  "crop":"apple",
  "bulletins":[ {"pest":"name-ko","risk":"LOW|MODERATE|HIGH|ALERT","since":"YYYY-MM-DD","summary":"1–2 lines ko"} ],
  "observations":[ {"area":"안동시","pest":"name-ko","metric":"트랩당마리수","code":"SS0128","value":93.6} ],
  "provenance":["NPMS-SVC31(YYYY-MM-DD)","NPMS-SVC53(YYYY-MM-DD)"]
}
```

*Drop encyclopedic pages, non-target crops, and historical counts.*

> Implementation note:  
> * Bulletins derive from **SVC31** (crop model).  
> * `observations` derive from **SVC51→SVC53** (예찰 목록 → 예찰 상세).  
> * For MVP we only resolve `insectKey` for Andong-si apples (predict code `00209`), filtering `sigunguCode` to 안동시.
> * If SVC51 lookup fails, fall back to `insectKey=202500209FT01060101322008` (2025 관찰포 8차).

---

## 3) Minimal Normalization

* **Time**: convert all timestamps to **ISO8601 KST**; keep `date` for daily.
* **Units**: `°C`, `mm`, `m/s`, `%`; radiation (if present) `W/m²`.
* **Keys**: adopt the unified field names above; retain each source in `provenance`.
* **Window**: keep **hourly ≤72h**, **daily up to D10**.

---

## 4) Merge Policy (Andong Apple)

* **Numeric daily + hourly**: use **Open‑Meteo** as primary across D0–D10; use `src="open-meteo"`.
* **KMA mid‑term summaries**: surface as `daily[].summary` and `daily[].precip_probability_pct` when available; do not overwrite numeric fields.
* **Warnings**: from **KMA** when accessible; otherwise omit (empty array).
* **Pest observations**: only include SVC53 rows whose `sigunguCode` matches 안동시; surface as `observations` alongside bulletins.
* **Pest hints**: raise deterministic advisories (non-binding). MVP trigger — 안동시 복숭아순나방(트랩당마리수, code `SS0127`) ≥ 10 → 방제 검토 권장 메시지 with NPMS SVC53 citation.
* Keep arrays **as provided** (no averaging); annotate each element with `src` where applicable.

---

## 5) Soft Hints (optional, deterministic, non‑binding)

Compute once to help the model, but **never force decisions**:

```json
{
  "soft_hints": {
    "rain_run_max_days": 2,           // longest run of daily precip_mm > 0
    "heat_hours_ge_33c": 6,           // sum from hourly t_c >= 33 (next 72h)
    "wind_hours_ge_10ms": 0,          // hourly wind_ms >= 10
    "wet_nights_count": 1,            // nights with rh_pct >= 90 for >=3h
    "diurnal_range_max": 12,          // max(tmax_c - tmin_c) in window
    "first_warning_type": "HEAT"|null // from KMA warnings if any
  }
}
```

*(If time is tight, omit `soft_hints` entirely.)*

---

## 6) Evidence Pack (final payload to LLM)

```json
{
  "profile": {"region":"Andong-si","crop":"apple","stage":"flowering"},
  "issued_at":"2025-10-29T09:00:00+09:00",
  "climate":{
    "horizon_days":10,
    "daily":[ ... D0–D10 merged ... ],
    "hourly":[ ... next ≤72h ... ],
    "warnings":[ ... KMA ... ],
    "provenance":[ "KMA(2025-10-29)", "Open-Meteo(2025-10-29)" ]
  },
  "pest":{
    "crop":"apple",
    "bulletins":[ {"pest":"갈색무늬병","risk":"MODERATE","since":"2025-10-27","summary":"강수 후 전엽기 환기·위생관리 강화"} ],
    "observations":[ {"area":"안동시","pest":"사과굴나방","metric":"트랩당마리수","code":"SS0128","value":93.6} ],
    "provenance":[ "NPMS-SVC31(2025-10-27)", "NPMS-SVC53(2025-10-27)" ]
  },
  "pest_hints":["안동시 복숭아순나방(트랩당마리수) 17.25마리 관측 — 10마리 이상으로 높음. 살충제 방제 검토를 권장합니다 (출처: NPMS SVC53)."],
  "soft_hints":{
    "rain_run_max_days":2,"heat_hours_ge_33c":6,"wind_hours_ge_10ms":0,"wet_nights_count":1,"diurnal_range_max":12,"first_warning_type":"HEAT"
  }
}
```

---

## 7) Aggregator Service Contract

**POST `/api/aggregate`**

* **Input**: `Profile`
* **Process**: resolve IDs → parallel fetch (**KMA mid‑term summaries, Open‑Meteo numeric, NPMS apple bulletins**) → minimal normalize → optional soft hints → **return evidence pack**
* **Output**: `EvidencePack` (above)

**Caching/TTL (suggested)**

* KMA short-range + warnings: **1–3h**
* Open-Meteo hourly/daily: **3h**
* NPMS bulletins: **12–24h**

**Fallbacks**

* KMA unavailable → proceed with Open‑Meteo numeric only; keep provenance.
* NPMS empty → `bulletins: []` (default to observation/hygiene guidance for apple).

**Demo Switch**

* `?demo=true` → serve scripted scenarios.

**Logging (minimal)**

* JSON line: `req_id, region, crop, fetched:{kma,om,npms}, cache_hit, duration_ms`.

---

## 8) LLM Prompt Contract (for reference)

* “Use **raw forecast** (Open‑Meteo numeric + KMA summaries) and **NPMS (apple) bulletins** as primary evidence.
  Soft hints are advisory; if hints conflict with raw data or warnings, **ignore hints**.
  Generate **Top‑3 actions with timing/trigger** for Andong‑si apple {stage} in plain Korean.
  **Cite one source+year per action**; **no pesticide/medical directives**.”

---

## 9) Non-Goals (MVP)

* No ET₀/soil models/price feeds; no MCP/tools; no microservices; no analytics stack. No multi‑region/crop handling.
