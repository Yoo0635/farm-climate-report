#!/bin/bash
# Docker 컨테이너 재시작

set -e

echo "🔄 Restarting Docker containers..."
docker compose restart

echo ""
echo "✅ Containers restarted!"
echo ""
echo "📊 Container status:"
docker compose ps

echo ""
echo "📝 View logs: ./scripts/docker-logs.sh"
