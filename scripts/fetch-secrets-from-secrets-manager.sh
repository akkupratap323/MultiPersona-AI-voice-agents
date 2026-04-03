#!/bin/bash
# Fetch secrets from AWS Secrets Manager and create .env file
# Run this on the Lightsail server during deployment

ENV_FILE="${1:-/home/ec2-user/nester-bot/.env}"
REGION="ap-south-1"
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
    --region "$REGION" \
    --query SecretString \
    --output text 2>/dev/null)

if [ -z "$SECRET_JSON" ]; then
    echo "❌ Failed to fetch secret from Secrets Manager"
    echo "   Check IAM permissions and secret name"
    exit 1
fi

echo "✅ Secret fetched"
echo "📝 Creating $ENV_FILE..."

# Convert JSON to .env format
# Use Python for reliable JSON parsing
python3 << PYTHON_SCRIPT > "$ENV_FILE"
import json
import sys

try:
    secret_data = json.loads('''$SECRET_JSON''')
    
    # Write header
    print("# Auto-generated from AWS Secrets Manager")
    print("# Do not edit manually - changes will be overwritten on next deploy")
    print("# Last updated: $(date)")
    print("")
    
    # Write all key-value pairs
    for key, value in sorted(secret_data.items()):
        if value:  # Only write non-empty values
            # Escape special characters in value
            value = str(value).replace('\\', '\\\\').replace('$', '\\$').replace('`', '\\`')
            print(f"{key}={value}")
    
    sys.exit(0)
except Exception as e:
    print(f"# Error parsing secret: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON_SCRIPT

if [ $? -ne 0 ]; then
    echo "❌ Failed to parse secret JSON"
    exit 1
fi

# Secure the file
chmod 600 "$ENV_FILE"

echo "✅ Secrets loaded from AWS Secrets Manager"
echo "📁 File: $ENV_FILE"
echo "🔒 Permissions: 600 (owner read/write only)"
echo ""
echo "📋 Loaded secrets:"
grep -E '^[A-Z_]+=' "$ENV_FILE" | cut -d= -f1 | sed 's/^/   - /'

