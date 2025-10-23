# Data Model: Personalized SMS Farm Brief MVP

**Feature**: /home/tomto/projects/farm-climate-reporter/specs/001-send-sms-brief/spec.md  
**Date**: 2025-10-22

## Entities

- Profile
  - id (string)
  - phone (string, E.164 for demo; pre‑authorized list)
  - region (string, e.g., KR: province/county)
  - crop (string)
  - stage (string)
  - language (string: "ko")
  - opt_in (boolean)

- Brief
  - id (string)
  - profile_id (string)
  - horizon_days (int, =14)
  - actions (array<Action>, length=3)
  - triggers (array<string>)
  - link_id (string)
  - date_range (string)
  - created_at (datetime)

- Action
  - title (string, Korean, senior‑friendly)
  - timing_window (string)
  - trigger (string)
  - icon (string, optional)
  - source_name (string)
  - source_year (int)

- Signal
  - type (enum: climate|pest)
  - code (string, e.g., HEATWAVE, RAIN_MULTI)
  - severity (string)
  - notes (string)

- Interaction
  - id (string)
  - phone (string)
  - keyword (string: "1"|"REPORT"|"CHANGE"|"STOP"|other)
  - received_at (datetime)
  - response (string)

- DraftReport
  - id (string)
  - brief_id (string)
  - content (string)  # flexible format
  - created_at (datetime)

- RefinedReport
  - id (string)
  - draft_id (string)
  - content (string)  # simplified Korean sentences
  - created_at (datetime)

## Relationships
- Profile 1—* Brief
- Brief *—* Action (embedded list)
- Brief *—* Signal (derived / associated)
- Phone 1—* Interaction
 - Brief 1—1 DraftReport (when LLM succeeds)
 - DraftReport 1—1 RefinedReport (when LLM succeeds)

## Validation Rules
- Exactly 3 actions per brief.
- Each action MUST include source_name and source_year.
- Icons optional; omit if SMS length risk detected.
- CHANGE flow prompts ≤2 messages; updates region/crop/stage only.
 - If LLM pipeline fails, no DraftReport/RefinedReport entities are created; send is aborted.

## State Notes
- Opt‑in out of scope for demo; profiles pre‑authorized.
- Interactions stored in memory for debugging during demo.
