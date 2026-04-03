#!/bin/bash
# Fetch secrets from AWS Secrets Manager and create .env file
# Run this on the Lightsail server during deployment

set -euo pipefail

ENV_FILE="${1:-/home/ec2-user/nester-bot/.env}"
AWS_REGION="${AWS_REGION:-ap-south-1}"
SECRET_NAME="nester/voice-bot/secrets"

echo "🔐 Fetching secrets from AWS Secrets Manager..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found"
    exit 1
fi

echo "📥 Downloading secrets from: $SECRET_NAME..."

# Fetch secret from Secrets Manager
SECRET_JSON=$(aws secretsmanager get-secret-value \
    --secret-id "$SECRET_NAME" \
    --region "$AWS_REGION" \
    --query SecretString \
    --output text 2>/dev/null)

if [ -z "$SECRET_JSON" ]; then
    echo "❌ Failed to fetch secret from Secrets Manager"
    echo "   Falling back to Parameter Store..."
    
    # Fallback to Parameter Store for backward compatibility
    # Use parameter prefix to fetch all at once (more efficient)
    echo "⚠️  Fetching from Parameter Store (fallback mode)..."
    PARAMS=$(aws ssm get-parameters \
        --names \
            "/nester/DEEPGRAM_API_KEY" \
            "/nester/OPENAI_API_KEY" \
            "/nester/GOOGLE_API_KEY" \
            "/nester/ELEVENLABS_API_KEY" \
            "/nester/ELEVENLABS_VOICE_ID" \
            "/nester/PINECONE_API_KEY" \
            "/nester/PINECONE_INDEX" \
            "/nester/PUBLIC_URL" \
            "/nester/LIGHTRAG_API_KEY" \
        --with-decryption \
        --region "$AWS_REGION" \
        --query 'Parameters[*].[Name,Value]' \
        --output text 2>/dev/null || echo "")
    
    # Parse parameters into variables
    while IFS=$'\t' read -r name value; do
        case "$name" in
            "/nester/DEEPGRAM_API_KEY") DEEPGRAM_API_KEY="$value" ;;
            "/nester/OPENAI_API_KEY") OPENAI_API_KEY="$value" ;;
            "/nester/GOOGLE_API_KEY") GOOGLE_API_KEY="$value" ;;
            "/nester/ELEVENLABS_API_KEY") ELEVENLABS_API_KEY="$value" ;;
            "/nester/ELEVENLABS_VOICE_ID") ELEVENLABS_VOICE_ID="$value" ;;
            "/nester/PINECONE_API_KEY") PINECONE_API_KEY="$value" ;;
            "/nester/PINECONE_INDEX") PINECONE_INDEX="$value" ;;
            "/nester/PUBLIC_URL") PUBLIC_URL="$value" ;;
            "/nester/LIGHTRAG_API_KEY") LIGHTRAG_API_KEY="$value" ;;
        esac
    done <<< "$PARAMS"
    
    cat > "$ENV_FILE" << EOF
# Auto-generated from AWS Parameter Store (fallback)
# Do not edit manually - changes will be overwritten on next deploy
# Last updated: $(date)

# Required API Keys
DEEPGRAM_API_KEY=$DEEPGRAM_API_KEY
OPENAI_API_KEY=$OPENAI_API_KEY
GOOGLE_API_KEY=$GOOGLE_API_KEY
ELEVENLABS_API_KEY=$ELEVENLABS_API_KEY
ELEVENLABS_VOICE_ID=$ELEVENLABS_VOICE_ID
LIGHTRAG_API_KEY=$LIGHTRAG_API_KEY

# Pinecone RAG Configuration
PINECONE_API_KEY=$PINECONE_API_KEY
PINECONE_INDEX=$PINECONE_INDEX

# Server Configuration
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=7860
WEBSOCKET_HOST=0.0.0.0
WEBSOCKET_PORT=8765
WEBSOCKET_SERVER=fast_api
PUBLIC_URL=$PUBLIC_URL

# Session Settings
SESSION_TIMEOUT=180
LOG_LEVEL=INFO
DOMAIN=3.6.64.48.nip.io
EOF
else
    echo "✅ Secret fetched from Secrets Manager"
    echo "📝 Creating $ENV_FILE..."
    
    # Convert JSON to .env format using Python
    # Write JSON to temp file first to avoid escaping issues
    TEMP_JSON=$(mktemp)
    echo "$SECRET_JSON" > "$TEMP_JSON"
    
    python3 << 'PYTHON_SCRIPT' > "$ENV_FILE"
import json
import sys
from datetime import datetime

try:
    # Read JSON from file
    with open(sys.argv[1], 'r') as f:
        secret_data = json.load(f)
    
    # Write header
    print("# Auto-generated from AWS Secrets Manager")
    print("# Do not edit manually - changes will be overwritten on next deploy")
    print(f"# Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # Write all key-value pairs
    for key, value in sorted(secret_data.items()):
        if value:  # Only write non-empty values
            # Escape special characters in value for shell
            value_str = str(value).replace('\\', '\\\\').replace('$', '\\$').replace('`', '\\`').replace('"', '\\"')
            print(f"{key}={value_str}")
    
    sys.exit(0)
except Exception as e:
    print(f"# Error parsing secret: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON_SCRIPT "$TEMP_JSON"
    
    rm -f "$TEMP_JSON"
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to parse secret JSON"
        exit 1
    fi
fi

# Secure the file
chmod 600 "$ENV_FILE"

echo "✅ Secrets loaded"
echo "📁 File: $ENV_FILE"
echo "🔒 Permissions: 600 (owner read/write only)"
echo ""
echo "📋 Loaded secrets:"
grep -E '^[A-Z_]+=' "$ENV_FILE" | cut -d= -f1 | sed 's/^/   - /'

