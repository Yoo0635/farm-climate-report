#!/bin/bash
# Docker 컨테이너 상태 확인

echo "📊 Docker Container Status"
echo "=========================="
echo ""

docker compose ps

echo ""
echo "💾 Disk Usage:"
docker compose exec app df -h | grep -E '(Filesystem|/app)'

echo ""
echo "🔍 Health Check:"
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
  echo "✅ API is healthy"
  curl -s http://localhost:8080/health | jq .
else
  echo "❌ API is not responding"
fi
