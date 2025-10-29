# API Aggregation Spec — **Raw + Soft Hints** (KMA · NPMS · Open-Meteo)

> Purpose: Backend fetches three sources, does **minimal normalization**, computes **non-binding soft hints**, and hands a single **evidence pack** to the LLM.
> Scope: **D0–D10** horizon; crops: **rice, lettuce, tomato**; monolithic FastAPI service.
> **IMPORTANT: This specification is a draft and is subject to change at any time. If there is a reasonable justification, you should plan outside the specification and then modify this document.**
---

## 0) Principles

* **No hard triggers.** The LLM reasons primarily from raw data.
* **Minimal normalize only**: time zone, units, and key names. No bias-correction/regridding.
* **Soft hints are advisory**; if they conflict with raw/warnings, the model must prefer raw.

---

## 1) Inputs & Identity

**Request (Profile)**

```json
{"region":"Gimcheon-si","crop":"tomato","stage":"flowering"}
```

**Resolver (derived once)**

* `lat, lon` (Open-Meteo)
* `kma_grid` (e.g., `{nx, ny}` or area code for short/mid-term)
* `npms_region_code` (region for bulletins)

*(For the hackathon, preload demo profiles with all three IDs.)*

---

## 2) External Fetchers & Fields to Keep

### A) **KMA** (primary for D0–D3 + all warnings)

Keep:

```json
{
  "issued_at": "ISO8601+09:00",
  "daily": [ {"date":"YYYY-MM-DD","tmax_c":33.1,"tmin_c":24.3,"precip_mm":12.0,"wind_ms":7.2} ],
  "hourly": [ {"ts":"ISO8601+09:00","t_c":31.5,"rh_pct":64,"wind_ms":5.1,"gust_ms":8.3,"precip_mm":0.2} ],
  "warnings": [ {"type":"HEAT|RAIN|WIND|COLD|TYPHOON","level":"WATCH|WARNING","from":"ISO","to":"ISO","area":"text"} ],
  "provenance": "KMA(YYYY-MM-DD)"
}
```

### B) **Open-Meteo** (primary D4–D10; hourly detail; fallback)

Keep (same keys/units as KMA):

```json
{
  "issued_at": "ISO8601",
  "daily": [ {"date":"YYYY-MM-DD","tmax_c":32.0,"tmin_c":23.0,"precip_mm":5.0,"wind_ms":6.0} ],
  "hourly":[ {"ts":"ISO8601","t_c":30.2,"rh_pct":60,"wind_ms":4.8,"gust_ms":7.5,"precip_mm":0.0,"swrad_wm2":650} ],
  "provenance": "Open-Meteo(YYYY-MM-DD)"
}
```

### C) **NPMS** (crop/region pest bulletins)

Keep (decision-driving only):

```json
{
  "issued_at":"ISO8601+09:00",
  "crop":"rice|lettuce|tomato",
  "bulletins":[ {"pest":"name-ko","risk":"LOW|MODERATE|HIGH|ALERT","since":"YYYY-MM-DD","summary":"1–2 lines ko"} ],
  "provenance":"NPMS(YYYY-MM-DD)"
}
```

*Drop encyclopedic pages, non-target crops, and historical counts.*

---

## 3) Minimal Normalization

* **Time**: convert all timestamps to **ISO8601 KST**; keep `date` for daily.
* **Units**: `°C`, `mm`, `m/s`, `%`; radiation (if present) `W/m²`.
* **Keys**: adopt the unified field names above; retain each source in `provenance`.
* **Window**: keep **hourly ≤72h**, **daily up to D10**.

---

## 4) Merge Policy (no hard rules)

* **D0–D3**: prefer **KMA** daily/hourly; fill gaps from Open-Meteo.
* **D4–D10**: prefer **Open-Meteo** daily; (optional) overlay KMA mid-term if already integrated.
* **Warnings**: always from **KMA** (carry verbatim).
* Keep arrays **as provided** (no averaging); mark which source supplied each day if needed (`daily[i].src` optional).

---

## 5) Soft Hints (optional, deterministic, non-binding)

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
  "profile": {"region":"Gimcheon-si","crop":"tomato","stage":"flowering"},
  "issued_at":"2025-10-29T09:00:00+09:00",
  "climate":{
    "horizon_days":10,
    "daily":[ ... D0–D10 merged ... ],
    "hourly":[ ... next ≤72h ... ],
    "warnings":[ ... KMA ... ],
    "provenance":[ "KMA(2025-10-29)","Open-Meteo(2025-10-29)" ]
  },
  "pest":{
    "crop":"tomato",
    "bulletins":[ {"pest":"잿빛곰팡이병","risk":"MODERATE","since":"2025-10-27","summary":"고온·고습 시 주의"} ],
    "provenance":[ "NPMS(2025-10-27)" ]
  },
  "soft_hints":{
    "rain_run_max_days":2,"heat_hours_ge_33c":6,"wind_hours_ge_10ms":0,"wet_nights_count":1,"diurnal_range_max":12,"first_warning_type":"HEAT"
  }
}
```

---

## 7) Aggregator Service Contract

**POST `/api/aggregate`**

* **Input**: `Profile`
* **Process**: resolve IDs → parallel fetch (**KMA, Open-Meteo, NPMS**) → minimal normalize → optional soft hints → **return evidence pack**
* **Output**: `EvidencePack` (above)

**Caching/TTL (suggested)**

* KMA short-range + warnings: **1–3h**
* Open-Meteo hourly/daily: **3h**
* NPMS bulletins: **12–24h**

**Fallbacks**

* KMA unavailable → use Open-Meteo only; keep provenance.
* NPMS empty → `bulletins: []` (the model should default to observation/hygiene guidance).

**Demo Switch**

* `?demo=true` → serve scripted scenarios.

**Logging (minimal)**

* JSON line: `req_id, region, crop, fetched:{kma,om,npms}, cache_hit, duration_ms`.

---

## 8) LLM Prompt Contract (for reference)

* “Use **raw forecast** (KMA/Open-Meteo) and **NPMS bulletins** as primary evidence.
  Soft hints are advisory; if hints conflict with raw data or warnings, **ignore hints**.
  Generate **Top-3 actions with timing/trigger** for {region,crop,stage} in plain Korean.
  **Cite one source+year per action**; **no pesticide/medical directives**.”

---

## 9) Non-Goals (MVP)

* No ET₀/soil models/price feeds; no MCP/tools; no microservices; no analytics stack.
