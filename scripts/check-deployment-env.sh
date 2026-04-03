#!/bin/bash
# Script to diagnose environment variable issues in deployment

echo "=== Checking Backend Container Environment Variables ==="
echo ""

# Check if backend container is running
if docker ps | grep -q nester-backend; then
    echo "✅ Backend container is running"
    echo ""

    echo "=== Checking Required Environment Variables ==="
    docker exec nester-backend bash -c '
        echo "RESEMBLE_API_KEY: ${RESEMBLE_API_KEY:0:10}..."
        echo "RESEMBLE_VOICE_UUID: $RESEMBLE_VOICE_UUID"
        echo "GOOGLE_API_KEY: ${GOOGLE_API_KEY:0:10}..."
        echo "DEEPGRAM_API_KEY: ${DEEPGRAM_API_KEY:0:10}..."
        echo "LIGHTRAG_API_KEY: ${LIGHTRAG_API_KEY:0:10}..."
        echo "LIGHTRAG_BASE_URL: $LIGHTRAG_BASE_URL"
    '

    echo ""
    echo "=== Backend Logs (last 50 lines) ==="
    docker logs nester-backend --tail 50

elif docker ps -a | grep -q nester-backend; then
    echo "⚠️  Backend container exists but is not running"
    echo ""
    echo "=== Container Status ==="
    docker ps -a | grep nester-backend
    echo ""
    echo "=== Backend Logs (last 100 lines) ==="
    docker logs nester-backend --tail 100
else
    echo "❌ Backend container not found"
    echo ""
    echo "=== Checking .env file location ==="
    if [ -f .env ]; then
        echo "✅ .env file found in current directory"
        echo ""
        echo "=== Environment variables in .env file (showing only key names) ==="
        grep -E "^[A-Z_]+" .env | cut -d= -f1
    else
        echo "❌ .env file not found in current directory"
        echo "Current directory: $(pwd)"
    fi
fi

echo ""
echo "=== Docker Compose Configuration ==="
echo "Checking which docker-compose file is being used..."
if [ -f docker-compose.ghcr.yml ]; then
    echo "✅ docker-compose.ghcr.yml found"
else
    echo "❌ docker-compose.ghcr.yml not found"
fi
