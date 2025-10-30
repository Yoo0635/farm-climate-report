#!/bin/bash
# Docker 컨테이너 완전 종료 (볼륨 제외)

set -e

echo "🗑️  Stopping and removing Docker containers..."
docker compose down

echo ""
echo "✅ Containers removed!"
echo ""
echo "💡 To also remove volumes, use: docker compose down -v"
