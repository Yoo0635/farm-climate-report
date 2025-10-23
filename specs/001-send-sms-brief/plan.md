# Implementation Plan: Personalized SMS Farm Brief MVP

**Branch**: `001-send-sms-brief` | **Date**: 2025-10-22 | **Spec**: /home/tomto/projects/farm-climate-reporter/specs/001-send-sms-brief/spec.md
**Input**: Feature specification from `/specs/001-send-sms-brief/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Deliver one personalized 2‑week farm action brief via SMS (top‑3 actions + timing +
triggers, icons optional) plus one public link to a Korean, senior‑friendly detail page.
LLM‑first: a two‑step pipeline generates a detailed report (LLM‑1, RAG context), then
refines it to simpler sentences for SMS (LLM‑2). The detailed report remains optional
on the detail page.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI; Jinja2 (detail page); pydantic; OpenAI SDK (RAG + LLM)  
**Storage**: None for MVP (in‑memory data/templates)  
**Testing**: On‑stage pass/fail checks; optional pytest for unit flows  
**Target Platform**: Cloud Run (monolith) + Firebase Hosting (public link)  
**Project Type**: single  
**Performance Goals**: Demo‑only; responsive on a single device  
**Constraints**: Korean language; SMS length; one SMS vendor; icons optional; no tracking stack; LLM failure aborts send  
**Scale/Scope**: ≤10 pre‑authorized demo recipients

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Single MVP: Exactly one working MVP within the 48-hour window.
- Channel: Deliver personalized farm action strategy via text + link only.
- Simplicity: KISS and YAGNI—no abstractions or features not needed now.
- Integrations: No microservices or extra vendors (one text provider max, or stub/manual).
- Ship-to-learn: Prefer choices that ship sooner and enable validation.

Gate Evaluation (pre‑design):
- Single MVP: PASS — one SMS + one link.
- Channel: PASS — SMS plus public link only.
- Simplicity: PARTIAL — LLM‑first adds one extra vendor; still a monolith.
- Integrations: EXCEPTION — add one LLM vendor (OpenAI) in addition to one SMS vendor; justified below.
- Ship‑to‑learn: PASS — binary on‑stage checks; no tracking stack.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
src/
├── api/                 # FastAPI routes (send brief, webhook, detail page)
├── services/            # brief generation (LLM/RAG), sms send, keyword handler
├── templates/           # Korean detail page template(s)
└── lib/                 # helpers (formatting, validation)

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Single project (monolith). Public detail page via template.
Cloud Run serves API; Firebase Hosting proxies public link if needed. One SMS vendor +
one LLM vendor (exception justified).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Extra vendor beyond SMS (LLM) | LLM‑first content is central for personalized, simplified KR text; templates alone insufficient | Template/rules‑only reduced quality; contradicts LLM‑first requirement |
