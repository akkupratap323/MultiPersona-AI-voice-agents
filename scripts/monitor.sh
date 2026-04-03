#!/bin/bash
# Container Health Monitor Script
# Run this to check the health of your deployment

echo "=== NesterVoiceAI Health Check ==="
echo ""

echo "1. Container Status:"
docker-compose -f docker-compose.https.yml ps
echo ""

echo "2. Resource Usage:"
docker stats --no-stream
echo ""

echo "3. System Memory:"
free -h
echo ""

echo "4. Disk Space:"
df -h /
echo ""

echo "5. Backend Health:"
curl -s http://localhost:7860/health | jq . 2>/dev/null || echo "Backend not responding"
echo ""

echo "6. Recent Backend Logs (last 20 lines):"
docker-compose -f docker-compose.https.yml logs --tail=20 backend | grep -E "ERROR|WARNING|INFO.*Initialized"
echo ""

echo "7. Container Restart Counts:"
docker inspect nester-backend nester-frontend nester-caddy --format='{{.Name}}: {{.RestartCount}}' 2>/dev/null
echo ""

echo "=== Health Check Complete ==="
