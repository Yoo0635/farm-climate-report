# Feature Specification: Personalized SMS Farm Brief MVP

**Feature Branch**: `001-send-sms-brief`  
**Created**: 2025-10-22  
**Status**: Draft  
**Input**: User description: "WHAT: A working MVP that sends a personalized 2-week farm action brief via SMS (Top-3 actions + timing + triggers + icon) and a single public detail link per brief; personalization axes: region · crop · growth stage. Each brief integrates climate and pest/disease signals into one message; after-event checklists are included in the detail page. Keyword replies (bi-directional): 1 = details, REPORT = latest brief, CHANGE = update profile, STOP = opt-out. Detail page shows: 3-line situation summary, date/trigger checklist, one “Plan B,” and named sources with year—clear, senior-friendly language. Scenarios to cover (at least three end-to-end): heatwave, multi-day rain, strong wind, low-temp swing, plus one high-value hard crop (e.g., ginseng/strawberry/tomato/grape) per chosen region. actions are observation/environment/work only; every action cites one source+year. Two-step delivery—concise SMS + link to depth—aligns with the user flow in the shared diagram. WHY: Reduce climate & pest risks by translating signals into “what to do, when,” cutting avoidable losses in sensitive, high-value crops. Stabilize income through timely mitigation and better quality/yield decisions. Bridge the digital divide for seniors and low-access users with SMS-first delivery and plain-language guidance. Be demo-ready for a 48-hour hackathon: narrowly scoped, auditable (sources+year), measurable (deliveries/opens/replies), and extensible post-event."

> Constitution Constraints (MVP):
> - Ship exactly one working MVP in 48 hours
> - Deliver via text message + link only
> - Enforce KISS and YAGNI—omit non-essential features
> - Avoid microservices and extra integrations/vendors
> - Bias to ship for rapid learning/validation

## Clarifications

### Session 2025-10-22

- Q: How should success be measured without real recipients? → A: Replace vanity KPIs
  with binary on‑stage demo checks (pass/fail for delivery, link opens, replies).
- Q: Should we implement any tracking/analytics? → A: No tracking stack. Keep focus on
  MVP value; only minimal runtime visibility (e.g., console logs) if needed for demo.
- Q: Must each action include an icon? → A: Optional. Include an icon only if SMS
  length and compatibility allow; otherwise omit icons.
- Q: Are pest/disease signals explicitly covered in tests? → A: Yes. Add an explicit
  acceptance scenario demonstrating a pest/disease risk integrated with climate context.
- Q: How many prompts may the CHANGE flow use? → A: 1–2 SMS prompts maximum (a mini wizard);
  prioritize minimal questions and no additional links.
- Q: Are RAG and LLM usage part of the MVP? → A: Yes. A two‑step LLM pipeline generates a
  detailed report first, then a second LLM refines it into simpler Korean sentences for the
  SMS. The detailed report remains available at the public link, and its format is flexible.
- Q: What is the fallback if the LLM pipeline fails? → A: Abort send and show explicit on‑stage
  failure; do not send a partial or cached brief.
 - Q: Which providers power the two LLM steps? → A: LLM‑1 uses OpenAI with RAG context;
  LLM‑2 uses Google Gemini for Korean‑friendly refinement.

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
   mention, optional icons if length allows, and one public link.
2. Multi‑day rain: Given a profile, when multi‑day rain is forecast, then the SMS contains
   prevention and after‑rain checks with timing and triggers plus one public link.
3. Strong wind: Given a profile, when strong wind is forecast, then the SMS contains tie‑down
   and damage inspection actions with timing and triggers plus one public link.
4. Low‑temperature swing: Given a profile, when low‑temp swing occurs, then the SMS contains
   protection and monitoring actions with timing/triggers plus one public link.
5. High‑value crop case: Given the chosen region and a designated high‑value crop,
   when a relevant signal applies, then the SMS includes crop‑specific actions and one link.
6. Pest/disease alert: Given a profile, when a relevant pest/disease risk is present
   (e.g., powdery mildew or rice blast), then the SMS integrates that signal with climate
   context, includes targeted actions with timing/triggers, optional icons, and one link.

---

### User Story 2 - View Detail Page (Priority: P2)

From the SMS link, the recipient opens a public detail page written in senior‑friendly
language. The page shows a concise 3‑line situation summary, a date/trigger checklist,
one “Plan B,” and named sources with year. The full detailed report generated by the
LLM pipeline is available on this page as an optional, flexible‑format section.

**Why this priority**: Completes the two‑step delivery and depth for auditability.

**Independent Test**: Open the link on a basic mobile browser to verify content elements.

**Acceptance Scenarios**:

1. Given the link in the SMS, when the recipient opens it, then the page shows a
   3‑line summary, date/trigger checklist, one Plan B, named sources with year, and an
   optional detailed report section.
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
3. Given a user, when they reply "CHANGE", then SMS prompts collect profile updates
   (region, crop, growth stage) using at most 1–2 prompts, with no additional links.
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
- Missing profile fields → Use defaults or prompt to complete minimal fields via SMS.
- Initial demo profile capture → Use preloaded test profiles; updates handled via CHANGE via SMS.
- High‑value crop not available for region → Fall back to default crop guidance and note
  the limitation.
- STOP received after message send → Confirm opt‑out immediately and suppress future sends.
- Accessibility → Ensure plain language without abbreviations or jargon in SMS/page.
 - LLM pipeline unavailable or errors → Abort SMS send and display explicit failure to the
   on‑stage operator; do not send partial, stale, or cached content.

**Assumptions (demo scope)**

- Messaging is in Korean for the demo audience.
- Region is fixed to South Korea; coverage includes common high‑value crops for Korea;
  default growth stage set per crop and adjustable via CHANGE prompts.
- Profile updates are handled via SMS prompts (no additional links for CHANGE).
- Opt‑in capture is out of scope for the hackathon demo; internal test numbers are
  pre‑authorized per team policy.

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST send exactly one concise SMS per brief that includes
  top‑3 actions, timing windows, triggers, and exactly one public link to a detail page;
  icons are optional and included only if SMS length/compatibility allows.
- **FR-002**: Each brief MUST be personalized by region, crop, and growth stage.
- **FR-003**: Each brief MUST integrate climate and pest/disease signals into a single message.
- **FR-004**: The detail page MUST include: (a) a 3‑line situation summary,
  (b) a date/trigger checklist, (c) one "Plan B", and (d) named sources with year
  for each action.
- **FR-005**: Keyword replies MUST function as follows: "1" returns the details link;
  "REPORT" returns the latest brief summary and link; "CHANGE" engages SMS prompts to
  update profile (region, crop, growth stage) using at most 1–2 prompts; "STOP" opts‑out,
  sends confirmation, and prevents further messages.
- **FR-006**: Each action MUST cite one named source with year;
- **FR-007**: No tracking/analytics stack is required. Acceptance is via binary on‑stage
  checks (delivery, link opens, keyword replies). Minimal runtime visibility (e.g., console
  logs) is sufficient for the demo.
- **FR-008**: The brief MUST cover a 2‑week horizon and clearly indicate timing windows.
- **FR-009**: MVP MUST demonstrate at least three end‑to‑end scenarios: heatwave,
  multi‑day rain, strong wind, low‑temperature swing; plus one case for a high‑value crop
  in the chosen region.
- **FR-010**: Language MUST be senior‑friendly and plain in Korean; messages MUST be readable
  on basic mobile devices.
 - **FR-012**: The system MUST generate a detailed report from climate and pest/disease
  signals using an LLM, then refine it via a second LLM pass into simpler Korean sentences
  suitable for SMS; the detailed report remains available at the public link.
- **FR-013**: SMS content MUST consist primarily of short, simple sentences that summarize
  the top‑3 actions with timing and triggers; the detail page MAY present a flexible report
  layout as long as required elements are present.
 - **FR-014**: If the LLM pipeline (generation or refinement) fails, the system MUST abort
  the send and present an explicit failure for the on‑stage demo operator; no partial or
  cached report/SMS may be delivered.
  

### Key Entities *(include if feature involves data)*

- **Profile**: Region, crop, growth stage, phone, opt‑in status.
- **Brief**: 2‑week horizon, top‑3 actions, triggers, personalization axes, link id.
- **Action**: Text, timing window, trigger condition, icon indicator, source name + year.
- **Signal**: Climate and pest/disease indicators that map to actions.
- **Interaction**: Inbound keyword (1/REPORT/CHANGE/STOP) and outbound response.
- **DraftReport**: LLM‑generated detailed text integrating signals and sources (flexible format).
- **RefinedReport**: Second‑pass LLM output simplified for readability; SMS extracts sentences
  from this version.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: On stage, the demo phone receives the SMS that includes top‑3 actions,
  timing, triggers, optional icons, and a single link (pass/fail).
- **SC-002**: The link opens on a basic mobile browser and shows the 3‑line summary,
  date/trigger checklist, one Plan B, and sources with year (pass/fail).
- **SC-003**: Replying "1" returns the details link; "REPORT" returns the latest brief
  summary and link; "CHANGE" completes updates within 1–2 prompts; "STOP" opts‑out with
  confirmation and suppresses future sends (pass/fail for each keyword).
- **SC-004**: All actions in SMS and detail page cite a named source and year (pass/fail).
- **SC-005**: Korean language is clear and senior‑friendly in both SMS and detail page
  during the demo walkthrough (pass/fail).

### Language and Localization

- All SMS messages and the detail page MUST be written in Korean and remain senior‑friendly,
  plain language.
