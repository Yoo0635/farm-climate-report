set -euo pipefail
cd "$(dirname "$0")/.."
: "${DEMO_RECIPIENT_NUMBER:?DEMO_RECIPIENT_NUMBER not set in .env}"
./scripts/send_sms.py --to "01022168618" --text "[테스트] 포맷터 기반 SMS 발송 OK?"
