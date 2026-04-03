#!/bin/bash
# Quick script to check server logs and diagnose issues
# Usage: bash scripts/check-server-logs.sh

set -e

echo "=========================================="
echo "🔍 SERVER LOGS DIAGNOSTIC"
echo "=========================================="
echo ""

# Check backend container logs
echo "=== Backend Container Logs (last 100 lines) ==="
docker logs --tail 100 nester-backend 2>&1 || echo "❌ Could not fetch backend logs"
echo ""

# Check for system prompt loading
echo "=== System Prompt Loading ==="
docker logs nester-backend 2>&1 | grep -i "system prompt\|system_prompt\|identity\|Using custom system prompt" | tail -10 || echo "No system prompt logs found"
echo ""

# Check for RAG errors
echo "=== RAG/LightRAG Errors ==="
docker logs nester-backend 2>&1 | grep -i "rag\|lightrag\|knowledge base\|error" | tail -15 || echo "No RAG errors found"
echo ""

# Check container status
echo "=== Container Status ==="
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' | grep -E "nester|NAME" || docker ps
echo ""

# Check what image is being used
echo "=== Backend Image Info ==="
docker inspect nester-backend 2>/dev/null | grep -i "image\|repo\|tag" | head -5 || echo "Could not inspect container"
echo ""

# Check config file
echo "=== Config File Check (system_prompt) ==="
docker exec nester-backend cat /app/app/config/config.yaml 2>/dev/null | grep -A 5 "system_prompt:" | head -10 || echo "Could not read config file"
echo ""

# Check environment variables
echo "=== Environment Variables ==="
docker exec nester-backend env 2>/dev/null | grep -E "PUBLIC_URL|GOOGLE_API_KEY|LIGHTRAG|WEBSOCKET_SERVER" | sed 's/\(API_KEY\)=.*/\1=***/' || echo "Could not check environment"
echo ""

# Check recent errors
echo "=== Recent Errors (last 20) ==="
docker logs --tail 200 nester-backend 2>&1 | grep -i "error\|exception\|failed\|traceback" | tail -20 || echo "No recent errors found"
echo ""

# Check WebSocket connection logs
echo "=== WebSocket Connection Logs ==="
docker logs --tail 50 nester-backend 2>&1 | grep -i "websocket\|session\|connected\|disconnected" | tail -10 || echo "No WebSocket logs found"
echo ""

echo "=========================================="
echo "✅ Diagnostic complete"
echo "=========================================="

