# Quickstart: Personalized SMS Farm Brief MVP

This guide demonstrates end-to-end flows for the hackathon MVP.

## Prerequisites
- Feature branch: 001-send-sms-brief
- Demo phones pre-authorized (opt-in out of scope)

## Trigger a Brief (demo)

Example JSON payload (LLM-first):
```json
{
  "phone": "+821012345678",
  "region": "KR/Seoul",
  "crop": "Strawberry",
  "stage": "Flowering",
  "scenario": "HEATWAVE"
}
```

Send (example):
```bash
curl -X POST https://api.example.com/api/briefs \
  -H 'Content-Type: application/json' \
  -d '{"phone":"+821012345678","region":"KR/Seoul","crop":"Strawberry","stage":"Flowering","scenario":"HEATWAVE"}'
```

Expected result:
- LLM generates a detailed report; second LLM refines sentences.
- One SMS arrives in Korean with top‑3 actions, timing, triggers, and one link.
- Opening the link shows the required elements plus an optional detailed report section.

## Inbound Keywords (demo)

```bash
curl -X POST https://api.example.com/api/sms/webhook \
  -H 'Content-Type: application/json' \
  -d '{"from":"+821012345678","to":"+82105551234","message":"REPORT"}'
```

Expected result:
- REPORT → latest brief + link
- 1 → resend detail link
- CHANGE → 1–2 SMS prompts to update profile
- STOP → confirmation and suppression of future sends

## On-Stage Checks (pass/fail)
- SMS delivery visible on device
- Link opens to 3‑line summary + checklist + Plan B + sources(year)
- Keywords behave as specified
- Korean language clear and senior‑friendly
