# Research & Decisions: Personalized SMS Farm Brief MVP

**Date**: 2025-10-22  
**Branch**: 001-send-sms-brief  
**Spec**: /home/tomto/projects/farm-climate-reporter/specs/001-send-sms-brief/spec.md

## Decisions

### 1) SMS Vendor (Korea)
- Decision: Naver Cloud SENS (single vendor)
- Rationale: Local provider with solid Korea coverage; aligns with “one SMS vendor only”.
- Alternatives considered: SOLAPI (good alternative); Twilio (global but unnecessary for KR MVP).

### 2) Architecture (Monolith + Hosting)
- Decision: One FastAPI monolith on Cloud Run; public detail link via Firebase Hosting (or Cloud Run route if simpler).
- Rationale: Single deployable artifact; keeps two‑step (SMS + link) simple; easy to demo.
- Alternatives considered: Cloud Functions; pure Cloud Run serving both API and HTML; accepted but Firebase Hosting optional.

### 3) RAG and LLM Usage
- Decision: Use LLM‑first pipeline: LLM‑1 generates detailed report from RAG context (OpenAI vector store + file_search/web_search); LLM‑2 refines into simpler Korean sentences for SMS.
- Rationale: Central to value and clarity; improves personalization and senior‑friendly wording.
- Alternatives considered: Templates/rules‑only (rejected—insufficient quality); Defer LLM (rejected—contradicts user direction).

### 4) Icons in SMS
- Decision: Optional; default OFF unless length/compatibility allows.
- Rationale: Avoid SMS truncation and rendering issues; keep core value in text.
- Alternatives considered: Mandatory icons; rejected due to length risk.

### 5) Measurements for Demo
- Decision: Binary on‑stage checks only (delivery, link opens, keyword replies). No tracking stack.
- Rationale: KISS/YAGNI; eliminates non‑essential logging/analytics work.
- Alternatives considered: CTR/open rates; rejected as vanity KPIs for demo.

### 6) Keyword CHANGE Flow
- Decision: Mini wizard via SMS prompts (1–2 prompts max), no extra links.
- Rationale: Keeps SMS‑first and minimizes friction.
- Alternatives considered: Link to profile page; rejected for MVP.

### 7) Language & Content Policy
- Decision: Korean, senior‑friendly wording; actions limited to observation/environment/work; each action cites source + year.
- Rationale: Accessibility, trust, and safety.
- Alternatives considered: English; rejected per target audience.

### 8) Scenarios
- Decision: Cover heatwave, multi‑day rain, strong wind, low‑temp swing; include at least one high‑value crop case for South Korea.
- Rationale: Demonstrates breadth and utility under common KR conditions.
- Alternatives considered: Fewer scenarios; accepted but we’ll meet the “≥3 + one crop” bar.

## Implications
- Constitution gates: PASS — monolith; one SMS vendor; no extra vendor (RAG deferred).
- Data: In‑memory store for demo (profiles, briefs, interactions) to avoid DB overhead.
- Operations: Console logs only for visibility; no dashboards.
- Security: Pre‑authorized test numbers; opt‑in out of scope.

## Open Items (post‑event extensions)
- Introduce RAG (OpenAI vector store) to scale content generation.
- Add analytics pipeline for real users (opt‑in, privacy, dashboards).
- Vendor abstraction for SMS provider portability.
