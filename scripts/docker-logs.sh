#!/bin/bash
# Docker 컨테이너 로그 확인

# 기본값: 모든 서비스 로그 tail
SERVICE="${1:-}"

if [ -z "$SERVICE" ]; then
  echo "📝 Viewing logs for all services (Ctrl+C to exit)..."
  echo ""
  docker-compose logs -f --tail=100
else
  echo "📝 Viewing logs for service: $SERVICE (Ctrl+C to exit)..."
  echo ""
  docker-compose logs -f --tail=100 "$SERVICE"
fi
