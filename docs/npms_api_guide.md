# NPMS Open API — Working Notes

Last updated: 2025-10-30

## 1. Overview
- Base endpoint: `http://ncpms.rda.go.kr/npmsAPI/service`
- Auth: every request requires `apiKey` issued by NPMS (농촌진흥청 농약안전정보시스템).
- Encoding: responses are UTF-8 JSON, but many string fields are percent-encoded and include HTML entities (`&nbsp;`). Decode before use.
- Cross-domain parameters (`proxyUrl`, `div_id`) are required even for server-side calls; they can be set to dummy values.

## 2. Verified Credential
- Working key (per user): `2025be4f96399ec56e61d4ebfc656acd6cf9`
  - Confirms access to crop/pest model feed (`serviceCode=SVC31`).
  - `serviceCode=SVC32` currently returns empty payloads (`{"service":{}}`); likely needs additional approval or different parameters.

## 3. Service Codes

### SVC31 — Crop/Pest Model Listing
Fetches crop metadata and active pest model outputs for the supported crops.

**Request Example**
```
GET http://ncpms.rda.go.kr/npmsAPI/service
    ?apiKey=YOUR_KEY
    &serviceCode=SVC31
    &proxyUrl=http://example.com/callback
    &div_id=result
    [&cropList=FC010101]   # optional: filter by crop code (comma-separated)
```

**Key Request Parameters**
| Name | Required | Description |
|------|----------|-------------|
| `apiKey` | ✔ | Issued NPMS API key. |
| `serviceCode` | ✔ | Use `SVC31`. |
| `proxyUrl` | ✔ | Callback URL placeholder; required even if unused. |
| `div_id` | ✔ | Target DOM id; accepted dummy value (e.g., `result`). |
| `cropList` | — | Optional crop code(s) to filter results (array encoded as comma-separated string). |

**Response Snapshot (abridged)**
```json
{
  "service": {
    "kncrListData": [
      {"kncrNm":"%EB%85%BC%EB%B2%BC", "kncrCode":"FC010101"},
      {"kncrNm":"%EA%B3%A0%EC%B6%94", "kncrCode":"VC011205"}
    ],
    "pestModelByKncrList": [
      {
        "kncrNm":"%EB%85%BC%EB%B2%BC",
        "dbyhsMdlNm":"%EC%84%B8%EA%B7%A0%EB%B2%BC%EC%95%8C%EB%A7%88%EB%A6%84%EB%B3%91%EC%B6%9C%EC%88%98%EC%8B%9C",
        "validAlarmRiskIdex":"3",
        "nowDrveDatetm":"2025110712",
        "pestConfigStr":"...color-coded segments..."
      }
    ]
  }
}
```

**Fields of Interest**
- `kncrListData`: crop codes and names (percent-encoded). Map to internal crop identifiers. Examples:
  - `FC010101`: 논벼
  - `VC011205`: 고추
  - `FT010601`: 사과
- `pestModelByKncrList`: pest model outputs per crop.
  - `kncrCode`: crop code matching `kncrListData`.
  - `dbyhsMdlNm`: pest/model name (percent-encoded).
  - `validAlarmRiskIdex`: integer risk flag (1–5). Lower numbers indicate higher urgency.
  - `pestConfigStr`: pipe-separated segments using `!+@+!` delimiters. Each segment encodes `(title, message, color hex)`; empty `title/message` placeholders appear at the ends.
  - `nowDrveDatetm`: issuance timestamp (`YYYYMMDDHH` or `YYYYMMDDHHMM`, KST).

**Risk Index Mapping (current usage)**
| `validAlarmRiskIdex` | Mapped Risk | Notes |
|----------------------|-------------|-------|
| 1 | `ALERT` | Highest urgency; colours often `FF0000`. |
| 2 | `HIGH` | Elevated risk; colours vary (`FF3C00`, `FFCC00`, etc.). |
| 3 | `MODERATE` | Watch/monitor level (`370FFF`, `0831FF`, etc.). |
| 4+ | `LOW` | Lower urgency or background guidance. |

**Observed Behaviours**
- Multiple segments may describe staged advice (e.g., 1세대/2세대 방제). Pick the segment associated with `validAlarmRiskIdex`.
- `pestConfigStr` often includes `&nbsp;`; replace with spaces after URL decoding.
- `cropList` filter works with codes (e.g., `cropList=FC010101` for rice), reducing payload size.
- Timestamps are all in KST; convert to ISO date as needed.

### SVC32 — Prediction Map (Unverified)
- Intended to deliver geospatial prediction layers.
- Requests with the current key respond with `{"service":{}}`.
- Required parameters per official guide: `width` (optional), `cropList` (array), but functionality could be locked.

### SVC51 — Observation Listing (예찰 목록)
- Returns observation runs (`insectKey`) per crop/예찰구분. Used as a precursor to SVC53.
- Key params: `searchKncrCode` (crop code), optional `searchPredictnSpchcknCode` (e.g. 관찰포 `00209`), `searchExaminYear`, pagination (`displayCount` ≤ 50).
- Helpful fields: `insectKey`, `predictnSpchcknCode`/`Nm`, `examinSpchcknCode`/`Nm`, `examinTmrd`, `inputStdrDatetm`.
- Sorting tip: sort by `inputStdrDatetm` (descending) and `examinTmrd` to obtain the latest run.

### SVC53 — Observation Detail (예찰 검색)
- Requires `insectKey` (from SVC51) and `sidoCode` (광역시/도 코드; 경북=47).
- Responds with `structList` entries per 시군구 (`sigunguNm`, `sigunguCode`).
- Each entry provides `dbyhsNm` (pest + metric), `inqireCnClCode` (metric code), `inqireValue` (numeric), enabling filtering to a target 시군구 (안동시=4717).
- Combine SVC31 (risk) + SVC53 (observed values) for richer pest context.

## 4. Integration Notes
- The codebase’s `NpmsFetcher` currently:
  - Requires `NPMS_API_KEY` or explicit key injection.
  - Supports rice (`FC010101`) mapping; lettuce/tomato placeholders exist and should be populated once codes are confirmed.
  - Decodes percent-encoding + HTML entities, selects the segment indicated by `validAlarmRiskIdex`, and maps risk levels to `LOW/MODERATE/HIGH/ALERT`.
  - Limits bulletins to a handful (top 5 by severity) and stamps provenance with current KST.
- Expand the `_CROP_CODE_MAP` when additional crop codes are verified (e.g., lettuce, tomato codes from NPMS documentation).

## 5. Troubleshooting
- Empty response: confirm `serviceCode` and `cropList`; SVC31 works without `cropList`.
- Unauthorized: ensure API key is approved for the desired service code; otherwise NPMS returns a generic error page.
- Parsing issues: apply `urllib.parse.unquote` then `html.unescape`, and collapse double spaces.
- Rate limiting has not been observed, but cache responses (12h TTL is reasonable) to avoid excessive hits.

## 6. Next Steps
- Validate SVC31 outputs for lettuce/tomato crops — locate the correct `kncrCode` or consult NPMS support.
- Investigate SVC32 enabling, or identify alternative endpoints for bulletin text (if richer narrative is required).
- Formalize unit tests around real-world samples (store anonymized fixtures) once policy allows.
