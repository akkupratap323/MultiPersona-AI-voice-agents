#!/bin/bash
# Start ngrok with custom domain (requires paid plan)
# For free users, use start-ngrok.sh instead

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

FASTAPI_PORT=${FASTAPI_PORT:-7860}

if [ -z "$NGROK_DOMAIN" ]; then
    echo "❌ NGROK_DOMAIN not set in .env"
    echo ""
    echo "For custom domains, add to .env:"
    echo "NGROK_DOMAIN=your-domain.ngrok-free.app"
    echo ""
    echo "Or use the free version: ./scripts/start-ngrok.sh"
    exit 1
fi

echo "🚀 Starting ngrok with custom domain: $NGROK_DOMAIN"
echo "=========================================="

ngrok http $FASTAPI_PORT \
    --domain=$NGROK_DOMAIN \
    --log=stdout \
    --log-level=info
