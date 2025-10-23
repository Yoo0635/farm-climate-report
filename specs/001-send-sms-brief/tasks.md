# Tasks: Personalized SMS Farm Brief MVP

**Input**: Design documents from `/specs/001-send-sms-brief/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL for this MVP. Acceptance is via on‑stage pass/fail checks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Constitution Check (Must pass before Phase 1)

- [X] T001 Validate single MVP: exactly one SMS + one link in specs/001-send-sms-brief/spec.md
- [X] T002 Verify channel constraint across docs (SMS + link only) in specs/001-send-sms-brief/contracts/openapi.yaml
- [X] T003 Confirm monolith and no tracking stack in specs/001-send-sms-brief/plan.md
- [X] T004 Record integrations: one SMS vendor = SOLAPI; LLM vendors = OpenAI (LLM‑1) + Gemini (LLM‑2) justified in specs/001-send-sms-brief/research.md
- [X] T005 Ensure on‑stage binary checks listed under Success Criteria in specs/001-send-sms-brief/spec.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T006 Create project structure per plan in src/ and tests/
- [X] T007 Create FastAPI app entrypoint in src/api/app.py
- [X] T008 Add dependencies manifest in requirements.txt (FastAPI, pydantic, Jinja2, OpenAI, Google‑GenAI)
- [X] T009 [P] Add environment template in .env.sample (OPENAI_API_KEY, GEMINI_API_KEY, SOLAPI_KEY/SECRET)
- [X] T010 Add minimal Cloud Run files in Dockerfile and cloudrun.yaml
- [X] T011 [P] Add base template in src/templates/detail.html

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [X] T012 Implement SOLAPI client in src/services/sms/solapi_client.py
- [X] T013 [P] Implement OpenAI LLM client (LLM‑1 + RAG hooks) in src/services/llm/openai_client.py
- [X] T014 [P] Implement Google Gemini client (LLM‑2) in src/services/llm/gemini_client.py
- [X] T015 Implement RAG store interface (vector store + file_search/web_search hooks) in src/services/llm/rag_store.py
- [X] T016 [P] Implement content policy checks (no pesticide/medical; require source+year) in src/lib/policy.py
- [X] T017 [P] Implement Korean formatting helpers in src/lib/format_ko.py
- [X] T018 [P] Define pydantic models for entities in src/lib/models.py (Profile, Brief, Action, Signal, Interaction, DraftReport, RefinedReport)

---

## Phase 3: User Story 1 - Receive Personalized SMS Brief (Priority: P1) 🎯 MVP

**Goal**: Send one personalized 2‑week brief via SMS in Korean (top‑3 actions + timing + triggers, optional icons) with one public link; integrate climate + pest signals.

**Independent Test**: POST /api/briefs with {phone, region, crop, stage} → phone receives SMS with required elements and single link; on LLM failure, send is aborted with explicit operator error.

### Implementation for User Story 1

- [X] T019 [US1] Implement BriefGenerator pipeline (RAG → LLM‑1 → LLM‑2) in src/services/briefs/generator.py
- [X] T020 [P] [US1] Implement SMS message builder (short, simple Korean sentences) in src/services/briefs/sms_builder.py
- [X] T021 [US1] Implement /api/briefs route in src/api/routes/briefs.py (validate input; call generator; abort on LLM failure)
- [X] T022 [P] [US1] Implement in‑memory store for brief/link mapping in src/services/store/memory_store.py
- [X] T023 [US1] Integrate SOLAPI send in src/services/sms/solapi_client.py (ensure exactly one SMS)
- [X] T024 [P] [US1] Add readability adjustments (line breaks/length guards) in src/lib/format_ko.py
- [X] T025 [P] [US1] Implement citation injector (source+year) in src/services/briefs/citations.py
- [X] T026 [US1] Enforce guards: exactly one SMS + one link; icons optional; enforce content policy in src/api/routes/briefs.py
- [X] T027 [P] [US1] Add scenario mapping (heatwave, rain, wind, low‑temp) in src/services/signals/mappings.py
- [X] T028 [P] [US1] Update quickstart demo with HEATWAVE example in specs/001-send-sms-brief/quickstart.md

---

## Phase 4: User Story 2 - View Detail Page (Priority: P2)

**Goal**: Public detail page shows 3‑line summary, date/trigger checklist (incl. after‑event), one Plan B, sources with year, and optional detailed report section.

**Independent Test**: Open the SMS link on a basic mobile browser → all required elements render in Korean; detailed report section present.

### Implementation for User Story 2

- [X] T029 [US2] Implement public detail route in src/api/routes/public.py (render detail.html)
- [X] T030 [US2] Implement detail template with required elements in src/templates/detail.html
- [X] T031 [P] [US2] Implement Plan B generator (simple rule) in src/services/briefs/plan_b.py
- [X] T032 [P] [US2] Implement link service (link/id creation and resolve) in src/services/links/link_service.py
- [X] T033 [P] [US2] Add minimal mobile‑friendly CSS in src/templates/static/style.css and include in template

---

## Phase 5: User Story 3 - Keyword Replies (Priority: P3)

**Goal**: Support keyword replies: 1 → details; REPORT → latest brief; CHANGE → profile update via 1–2 SMS prompts; STOP → opt‑out.

**Independent Test**: POST /api/sms/webhook with each keyword → correct behavior and replies; STOP suppresses further sends.

### Implementation for User Story 3

- [X] T034 [US3] Implement inbound webhook /api/sms/webhook in src/api/routes/webhook.py (normalize SOLAPI payload)
- [X] T035 [US3] Implement keyword handler in src/services/keywords/handler.py (dispatch 1/REPORT/CHANGE/STOP)
- [X] T036 [P] [US3] Implement CHANGE mini‑wizard (≤2 prompts) in src/services/keywords/change_flow.py
- [X] T037 [P] [US3] Implement opt‑out state (STOP) in src/services/store/memory_store.py
- [X] T038 [US3] Send replies via SOLAPI in src/services/sms/solapi_client.py
- [X] T039 [P] [US3] Implement latest brief retriever in src/services/briefs/retriever.py
- [X] T040 [P] [US3] Implement brief summarizer for REPORT in src/services/briefs/summarizer.py

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041 Update AGENTS.md with active technologies and recent changes in AGENTS.md
- [X] T042 Run content policy review (no pesticide/medical; citations present) in src/lib/policy.py
- [X] T043 Add demo smoke script to drive flows in scripts/demo_smoke.sh
- [X] T044 Add Dockerfile and cloudrun.yaml for deployment (Cloud Run) in Dockerfile, cloudrun.yaml
- [X] T045 Add Firebase Hosting config and public assets in firebase.json, public/404.html
- [X] T046 Add LLM credentials/setup doc in docs/llm-config.md
- [X] T047 Add Korean style guide for authors in docs/ko-style-guide.md

---

## Dependencies & Execution Order

- Setup (Phase 1) → Foundational (Phase 2) → US1 (P1) → US2 (P2) → US3 (P3) → Polish
- US1 depends on Foundational completion
- US2 depends on US1 (needs stored brief + link)
- US3 depends on Foundational (webhook + sms) and benefits from US1 (latest brief)

## Parallel Opportunities

- Foundational [P]: T013, T014, T016, T017, T018
- US1 [P]: T020, T022, T024, T025, T027, T028
- US2 [P]: T031, T032, T033
- US3 [P]: T036, T037, T039, T040

## Implementation Strategy

- MVP first: Complete US1 end‑to‑end before US2/US3.
- Keep report format flexible in detail page; ensure SMS remains concise.
- Abort on LLM failure; do not send partial/cached content.
