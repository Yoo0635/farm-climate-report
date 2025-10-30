#!/bin/bash
# Docker 컨테이너 시작

set -e

echo "🚀 Starting Docker containers..."
docker compose up -d

echo ""
echo "✅ Containers started!"
echo ""
echo "📊 Container status:"
docker compose ps

echo ""
echo "🔗 Access URLs:"
echo "  - API: http://localhost:8080"
echo "  - Health: http://localhost:8080/health"
echo "  - Docs: http://localhost:8080/docs"
echo ""
echo "📝 View logs: ./scripts/docker-logs.sh"
