#!/bin/bash
# Start ngrok tunnel for NesterVoiceAI
# Creates a public HTTPS URL for the bot

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Get ports from config or use defaults
FASTAPI_PORT=${FASTAPI_PORT:-7860}

echo "🚀 Starting ngrok tunnel for NesterVoiceAI"
echo "=========================================="
echo ""
echo "FastAPI port: $FASTAPI_PORT"
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok not found. Please run: ./scripts/setup-ngrok.sh"
    exit 1
fi

# Start ngrok tunnel
echo "Starting ngrok tunnel..."
echo "Press Ctrl+C to stop"
echo ""

# Use ngrok to expose the FastAPI server
# --log=stdout sends logs to terminal
# http starts an HTTP tunnel (ngrok automatically provides HTTPS)
ngrok http $FASTAPI_PORT \
    --log=stdout \
    --log-level=info \
    --region=us
