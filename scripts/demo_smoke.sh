#!/usr/bin/env bash
set -euo pipefail

# Load .env if present (export all)
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

API_BASE=${API_BASE:-"http://localhost:8000"}

to_e164() {
  local num="$1"
  if [[ -z "$num" ]]; then echo ""; return; fi
  if [[ "$num" == +* ]]; then echo "$num"; return; fi
  # assume KR local format starting with 0
  local stripped=${num#0}
  echo "+82${stripped}"
}

# Recipient number priority: PHONE env > DEMO_RECIPIENT_NUMBER > default
RAW_RECIPIENT=${PHONE:-${DEMO_RECIPIENT_NUMBER:-"+821012345678"}} || true
RECIPIENT="$(to_e164 "$RAW_RECIPIENT")"

# Derive service number (the number users text to) from .env if available
# If SOLAPI_SENDER_NUMBER is local format (e.g., 01012345678), convert to E.164 (+82...)
RAW_SENDER=${SOLAPI_SENDER_NUMBER:-"01000000000"}
SERVICE_TO="$(to_e164 "$RAW_SENDER")"

echo "→ Triggering brief (to: $RECIPIENT)"
curl -sS -X POST "$API_BASE/api/briefs" \
  -H 'Content-Type: application/json' \
  -d '{"phone":"'$RECIPIENT'","region":"KR/Seoul","crop":"Strawberry","stage":"Flowering","scenario":"HEATWAVE"}' | jq

echo "→ Simulating REPORT keyword (from: $RECIPIENT → to: $SERVICE_TO)"
curl -sS -X POST "$API_BASE/api/sms/webhook" \
  -H 'Content-Type: application/json' \
  -d '{"from":"'$RECIPIENT'","to":"'$SERVICE_TO'","message":"REPORT"}' | jq
