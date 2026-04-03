#!/bin/bash
# Add RESEMBLE_API_KEY and RESEMBLE_VOICE_UUID to AWS Secrets Manager
# This script updates the existing secret with new keys

set -e

REGION="ap-south-1"
SECRET_NAME="nester/voice-bot/secrets"

echo "🔐 Adding Resemble AI secrets to AWS Secrets Manager"
echo "===================================================="
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Install it first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Run: aws configure"
    exit 1
fi

echo "✅ AWS CLI configured"
echo "📍 Region: $REGION"
echo "🔑 Secret name: $SECRET_NAME"
echo ""

# Check if secret exists
if ! aws secretsmanager describe-secret --secret-id "$SECRET_NAME" --region "$REGION" &>/dev/null; then
    echo "❌ Secret '$SECRET_NAME' does not exist"
    echo "   Please run migrate-to-secrets-manager.sh first to create the secret"
    exit 1
fi

echo "📥 Fetching current secret..."
CURRENT_SECRET=$(aws secretsmanager get-secret-value \
    --secret-id "$SECRET_NAME" \
    --region "$REGION" \
    --query SecretString \
    --output text 2>/dev/null)

if [ -z "$CURRENT_SECRET" ]; then
    echo "❌ Failed to fetch current secret"
    exit 1
fi

echo "✅ Current secret fetched"
echo ""

# Read new values from .env file
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env file not found in current directory"
    exit 1
fi

RESEMBLE_API_KEY=$(grep "^RESEMBLE_API_KEY=" "$ENV_FILE" | cut -d= -f2 | sed 's/^"\(.*\)"$/\1/' | sed "s/^'\(.*\)'$/\1/")
RESEMBLE_VOICE_UUID=$(grep "^RESEMBLE_VOICE_UUID=" "$ENV_FILE" | cut -d= -f2 | sed 's/^"\(.*\)"$/\1/' | sed "s/^'\(.*\)'$/\1/")

if [ -z "$RESEMBLE_API_KEY" ] || [ -z "$RESEMBLE_VOICE_UUID" ]; then
    echo "❌ Could not find RESEMBLE_API_KEY or RESEMBLE_VOICE_UUID in .env file"
    exit 1
fi

echo "📝 New secrets to add:"
echo "   RESEMBLE_API_KEY: ${RESEMBLE_API_KEY:0:10}... (hidden)"
echo "   RESEMBLE_VOICE_UUID: $RESEMBLE_VOICE_UUID"
echo ""

# Update JSON with new keys using Python
UPDATED_SECRET=$(python3 << PYTHON_SCRIPT
import json
import sys

try:
    # Parse current secret
    current_data = json.loads('''$CURRENT_SECRET''')
    
    # Add new keys
    current_data['RESEMBLE_API_KEY'] = '''$RESEMBLE_API_KEY'''
    current_data['RESEMBLE_VOICE_UUID'] = '''$RESEMBLE_VOICE_UUID'''
    
    # Convert back to JSON
    print(json.dumps(current_data))
    sys.exit(0)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON_SCRIPT
)

if [ $? -ne 0 ]; then
    echo "❌ Failed to update secret JSON"
    exit 1
fi

echo "🔄 Updating secret in AWS Secrets Manager..."
aws secretsmanager update-secret \
    --secret-id "$SECRET_NAME" \
    --secret-string "$UPDATED_SECRET" \
    --region "$REGION" \
    > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ Secret updated successfully!"
    echo ""
    echo "📋 Updated secret details:"
    echo "   Name: $SECRET_NAME"
    echo "   Region: $REGION"
    echo "   New keys added: RESEMBLE_API_KEY, RESEMBLE_VOICE_UUID"
    echo ""
    echo "🔍 Verify secret:"
    echo "   aws secretsmanager get-secret-value --secret-id $SECRET_NAME --region $REGION --query SecretString --output text | python3 -m json.tool | grep RESEMBLE"
else
    echo "❌ Failed to update secret"
    exit 1
fi
