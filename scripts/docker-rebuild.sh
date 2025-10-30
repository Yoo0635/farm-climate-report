#!/bin/bash
# Docker 이미지 재빌드 및 컨테이너 재시작

set -e

echo "🔨 Rebuilding Docker images..."
docker-compose down
docker-compose build --no-cache

echo ""
echo "🚀 Starting containers..."
docker-compose up -d

echo ""
echo "✅ Rebuild complete!"
echo ""
echo "📊 Container status:"
docker-compose ps

echo ""
echo "📝 View logs: ./scripts/docker-logs.sh"
