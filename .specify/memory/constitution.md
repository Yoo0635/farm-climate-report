<!--
Sync Impact Report

- Version change: N/A → 1.0.0
- Modified principles: (template placeholders replaced with concrete rules)
- Added sections: Implementation Constraints; Development Workflow
- Removed sections: None
- Templates requiring updates:
  - ✅ .specify/templates/plan-template.md (Constitution Check gates aligned)
  - ✅ .specify/templates/spec-template.md (Constitution constraints callout)
  - ✅ .specify/templates/tasks-template.md (Constitution check tasks added)
  - ⚠ None pending
- Follow-up TODOs:
  - TODO(RATIFICATION_DATE): Original adoption date unknown; set when known.
-->

# Farm Climate Reporter Constitution

## Core Principles

### I. Single MVP Delivery (48 hours)
- The team MUST ship exactly one working MVP during the 48-hour window.
- The MVP MUST deliver a personalized farm action strategy via a text message plus a link.
- Any feature not required to achieve this outcome MUST be excluded.
Rationale: Tight timebox demands ruthless focus on a single outcome users can try.

### II. Text + Link Channel Only
- Delivery MUST be text-first (e.g., SMS or equivalent text channel) containing a link.
- No additional UI channels (web apps beyond the linked page, mobile apps, chatbots) are allowed for the MVP.
- The link target MUST be minimal and readable on a basic mobile browser.
Rationale: A single, lightweight channel accelerates delivery and reduces risk.

### III. KISS and YAGNI (Non‑Negotiable)
- Simplicity is mandatory: prefer the smallest working approach over “nice to have” designs.
- The product MUST include only features needed now; defer all speculative work.
- Code and architecture MUST avoid abstractions, patterns, or layers not immediately required.
Rationale: Reduces cognitive load and increases delivery speed and learning.

### IV. No Extensions or Extra Integrations
- No microservices, message buses, or additional vendors unless essential to send the text + link.
- Any deviation (extensions, exceptions, vendor sprawl) MUST be cut immediately.
- If a vendor is required for text delivery, only one provider is allowed; otherwise stub or manual sends.
Rationale: Integration overhead and service sprawl kill hackathon velocity.

### V. Rapid Learning and Validation
- Bias decisions toward shipping and getting user feedback within the hackathon.
- MVP success MUST be demonstrable end-to-end with a simple, repeatable test.
- Capture only minimal signals needed to validate value (e.g., delivered, link opened, basic response).
Rationale: The point of the MVP is validated learning, not completeness.

## Implementation Constraints

- Architecture: Single codebase, single deployable artifact (monolith) for the MVP.
- Data: Use the simplest persistence possible (file or in-memory) unless durability is essential.
- Dependencies: Add only what is strictly necessary to deliver the text + link flow.
- Environments: One environment is sufficient during the hackathon; manual verification allowed.
- Testing: Minimal tests that prove the end-to-end outcome; exhaustive suites are out of scope.
- Operations: Logging sufficient to verify delivery and link usage; full observability not required.

## Development Workflow

- Constitution Check (gate): Before work starts, confirm the solution:
  1) produces a personalized strategy, 2) sends it via text + link,
  3) avoids extra integrations/services, 4) remains the simplest approach.
- Cut Rule: Any proposed deviation is removed immediately or postponed beyond the MVP.
- Decision Policy: When in doubt, choose the path that ships sooner with less code.
- Review: Pull requests MUST include a statement of compliance with Core Principles and Constraints.

## Governance

- Authority: This constitution governs all work during the hackathon.
- Amendments: Allowed only by team consensus documented in this file with a version bump and rationale.
- Versioning: Semantic—MAJOR for incompatible rule changes; MINOR for new principles/sections;
  PATCH for clarifications that don’t change meaning.
- Compliance: Reviewers MUST block changes that violate principles unless accompanied by an approved amendment.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): Original adoption date unknown | **Last Amended**: 2025-10-22
