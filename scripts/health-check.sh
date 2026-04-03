#!/bin/bash
# Health check script for post-deployment verification
# Returns 0 if healthy, non-zero if unhealthy

set -euo pipefail

PUBLIC_URL="${PUBLIC_URL:-}"
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-/health}"
MAX_RETRIES="${MAX_RETRIES:-5}"
RETRY_DELAY="${RETRY_DELAY:-10}"

if [ -z "$PUBLIC_URL" ]; then
    echo "❌ PUBLIC_URL not set"
    exit 1
fi

HEALTH_URL="${PUBLIC_URL}${HEALTH_ENDPOINT}"

echo "🔍 Health check: $HEALTH_URL"

for i in $(seq 1 "$MAX_RETRIES"); do
    echo "Attempt $i/$MAX_RETRIES..."
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 --insecure "$HEALTH_URL" || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ Health check passed (HTTP $HTTP_CODE)"
        exit 0
    else
        echo "⚠️  Health check failed (HTTP $HTTP_CODE)"
        if [ $i -lt $MAX_RETRIES ]; then
            echo "Retrying in ${RETRY_DELAY}s..."
            sleep "$RETRY_DELAY"
        fi
    fi
done

echo "❌ Health check failed after $MAX_RETRIES attempts"
exit 1

