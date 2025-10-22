# Feature Specification: Personalized SMS Farm Brief MVP

**Feature Branch**: `001-send-sms-brief`  
**Created**: 2025-10-22  
**Status**: Draft  
**Input**: User description: "WHAT: A working MVP that sends a personalized 2-week farm action brief via SMS (Top-3 actions + timing + triggers + icon) and a single public detail link per brief; personalization axes: region · crop · growth stage. Each brief integrates climate and pest/disease signals into one message; after-event checklists are included in the detail page. Keyword replies (bi-directional): 1 = details, REPORT = latest brief, CHANGE = update profile, STOP = opt-out. Detail page shows: 3-line situation summary, date/trigger checklist, one “Plan B,” and named sources with year—clear, senior-friendly language. Scenarios to cover (at least three end-to-end): heatwave, multi-day rain, strong wind, low-temp swing, plus one high-value hard crop (e.g., ginseng/strawberry/tomato/grape) per chosen region. Trust & safety (content policy): no pesticide/medical directives; actions are observation/environment/work only; every action cites one source+year. Two-step delivery—concise SMS + link to depth—aligns with the user flow in the shared diagram. WHY: Reduce climate & pest risks by translating signals into “what to do, when,” cutting avoidable losses in sensitive, high-value crops. Stabilize income through timely mitigation and better quality/yield decisions. Bridge the digital divide for seniors and low-access users with SMS-first delivery and plain-language guidance. Be demo-ready for a 48-hour hackathon: narrowly scoped, auditable (sources+year), measurable (deliveries/opens/replies), and extensible post-event."

> Constitution Constraints (MVP):
> - Ship exactly one working MVP in 48 hours
> - Deliver via text message + link only
> - Enforce KISS and YAGNI—omit non-essential features
> - Avoid microservices and extra integrations/vendors
> - Bias to ship for rapid learning/validation

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Receive Personalized SMS Brief (Priority: P1)

Send a single, concise SMS that summarizes a 2‑week farm action brief and includes a
public link to details. The brief is personalized by region, crop, and growth stage and
integrates climate and pest/disease signals into one message.

**Why this priority**: This is the core value proposition and must work end‑to‑end for demo.

**Independent Test**: Provide a profile (region, crop, growth stage) and trigger a brief.
Verify one SMS arrives containing top‑3 actions with timing and triggers and exactly one link.

**Acceptance Scenarios**:

1. Heatwave: Given a profile, when a heatwave signal applies, then the SMS contains
   top‑3 actions (e.g., shade, irrigation timing, canopy checks), timing windows, trigger
   mention, one icon per action, and one public link.
2. Multi‑day rain: Given a profile, when multi‑day rain is forecast, then the SMS contains
   prevention and after‑rain checks with timing and triggers plus one public link.
3. Strong wind: Given a profile, when strong wind is forecast, then the SMS contains tie‑down
   and damage inspection actions with timing and triggers plus one public link.
4. Low‑temperature swing: Given a profile, when low‑temp swing occurs, then the SMS contains
   protection and monitoring actions with timing/triggers plus one public link.
5. High‑value crop case: Given the chosen region and a designated high‑value crop,
   when a relevant signal applies, then the SMS includes crop‑specific actions and one link.

---

### User Story 2 - View Detail Page (Priority: P2)

From the SMS link, the recipient opens a public detail page written in senior‑friendly
language with a 3‑line situation summary, a date/trigger checklist, one “Plan B,” and
named sources with year.

**Why this priority**: Completes the two‑step delivery and depth for auditability.

**Independent Test**: Open the link on a basic mobile browser to verify content elements.

**Acceptance Scenarios**:

1. Given the link in the SMS, when the recipient opens it, then the page shows a
   3‑line summary, date/trigger checklist, one Plan B, and named sources with year.
2. Given the page, when the recipient scrolls top‑to‑bottom, then content remains readable
   and understandable without technical jargon.

---

### User Story 3 - Keyword Replies (Priority: P3)

Support simple, bi‑directional keyword replies: 1 = details, REPORT = latest brief,
CHANGE = update profile, STOP = opt‑out.

**Why this priority**: Enables quick user actions while keeping SMS concise.

**Independent Test**: Send each keyword from a test device and verify the appropriate response.

**Acceptance Scenarios**:

1. Given a received brief, when the user replies "1", then they receive the details
   link again and guidance to open it.
2. Given an active profile, when the user replies "REPORT", then they receive the latest
   brief summary and link.
3. Given a user, when they reply "CHANGE", then they receive a link to update profile
   (region, crop, growth stage) [NEEDS CLARIFICATION: CHANGE flow via link vs SMS prompts].
4. Given any user, when they reply "STOP", then they receive a confirmation and no further
   messages are sent until they re‑opt in, and the system records opt‑out.

---

[Add more user stories as needed, each with an assigned priority]

### Edge Cases

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right edge cases.
-->

- Unrecognized keyword → Send brief help text with supported keywords.
- Link cannot be opened → Offer to resend link; keep SMS minimal.
- Missing profile fields → Use defaults or prompt to complete minimal fields
  [NEEDS CLARIFICATION: Initial profile capture path for demo participants].
- High‑value crop not available for region → Fall back to default crop guidance and note
  the limitation.
- STOP received after message send → Confirm opt‑out immediately and suppress future sends.
- Accessibility → Ensure plain language without abbreviations or jargon in SMS/page.

**Assumptions (demo scope)**

- English‑only messaging for the demo audience.
- Exactly one region and one high‑value crop will be selected for the demo cohort
  [NEEDS CLARIFICATION: which region + crop + growth stage].
- CHANGE will return a link to a minimal profile update page unless a pure SMS flow is chosen.

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST send exactly one concise SMS per brief that includes
  top‑3 actions, timing windows, triggers, one icon per action, and exactly one
  public link to a detail page.
- **FR-002**: Each brief MUST be personalized by region, crop, and growth stage.
- **FR-003**: Each brief MUST integrate climate and pest/disease signals into a single message.
- **FR-004**: The detail page MUST include: (a) a 3‑line situation summary,
  (b) a date/trigger checklist, (c) one "Plan B", and (d) named sources with year
  for each action.
- **FR-005**: Keyword replies MUST function as follows: "1" returns the details link;
  "REPORT" returns the latest brief summary and link; "CHANGE" returns a profile update path
  [NEEDS CLARIFICATION: link to simple page vs SMS prompts]; "STOP" opts‑out, sends confirmation,
  and prevents further messages.
- **FR-006**: Each action MUST cite one named source with year; no pesticide/medical directives—
  actions are observation/environment/work only (content policy enforced).
- **FR-007**: System MUST capture minimal metrics needed for validation: deliveries,
  link opens, and keyword replies.
- **FR-008**: The brief MUST cover a 2‑week horizon and clearly indicate timing windows.
- **FR-009**: MVP MUST demonstrate at least three end‑to‑end scenarios: heatwave,
  multi‑day rain, strong wind, low‑temperature swing; plus one case for a high‑value crop
  in the chosen region.
- **FR-010**: Language MUST be senior‑friendly and plain; messages MUST be readable on basic
  mobile devices.
- **FR-011**: Demo participants MUST be explicitly opted‑in for SMS communication prior to
  receiving any message [NEEDS CLARIFICATION: opt‑in method for demo].

### Key Entities *(include if feature involves data)*

- **Profile**: Region, crop, growth stage, phone, opt‑in status.
- **Brief**: 2‑week horizon, top‑3 actions, triggers, personalization axes, link id.
- **Action**: Text, timing window, trigger condition, icon indicator, source name + year.
- **Signal**: Climate and pest/disease indicators that map to actions.
- **Interaction**: Inbound keyword (1/REPORT/CHANGE/STOP) and outbound response.
- **Metrics**: Delivery status, link opens, keyword reply counts.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: ≥95% of opted‑in demo recipients receive the brief on first send.
- **SC-002**: ≥60% of recipients open the detail link during the demo window.
- **SC-003**: ≥40% of recipients who open the link send a supported keyword reply (1 or REPORT).
- **SC-004**: 100% of STOP replies result in confirmation and suppression of any further sends.
- **SC-005**: 100% of actions in the brief and detail page cite a named source and year;
  zero content policy violations.
