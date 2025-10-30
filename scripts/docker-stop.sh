#!/bin/bash
# Docker 컨테이너 중지

set -e

echo "🛑 Stopping Docker containers..."
docker-compose stop

echo ""
echo "✅ Containers stopped!"
echo ""
docker-compose ps
