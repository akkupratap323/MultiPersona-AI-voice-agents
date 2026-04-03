#!/bin/bash
# Migrate secrets from .env file to AWS Secrets Manager
# Run this ONCE from your local machine to migrate all secrets

set -e

echo "🔐 Migrating secrets to AWS Secrets Manager"
echo "==========================================="
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

REGION="ap-south-1"
SECRET_NAME="nester/voice-bot/secrets"

echo "✅ AWS CLI configured"
echo "📍 Region: $REGION"
echo "🔑 Secret name: $SECRET_NAME"
echo ""

# Check if secret already exists
if aws secretsmanager describe-secret --secret-id "$SECRET_NAME" --region "$REGION" &>/dev/null; then
    echo "⚠️  Secret '$SECRET_NAME' already exists"
    read -p "Do you want to update it? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
    UPDATE_EXISTING=true
else
    UPDATE_EXISTING=false
fi

echo ""
echo "📥 Fetching current secrets from Lightsail server..."
echo ""

# SSH to server and get .env file
SSH_KEY='-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAzCUBJtu9zIaWp5q2PRlLjqxXJpqb2kUc+bDqf3jxg4iCoHed
dARdnL0Ojx4FGQUQkhu+vvCV8sDAF2SZ1p51MM9Q7R5wzMAGMQr+ntnJnk4OSQTb
RSgK5OTgF9C/XZU4mqkpgRFR8dhJYtoqyDoeslr1r6Ze7cKCWj9Miu2RJatVLK1Z
nuJG2I2UNDWbUx1QaMo3QmeP3BiIRIenlu18oTfydMjEugOiR0g9tza2HzaE5a7J
HDOqxkxJ6qmubCZ5GCasWBs5gr6rHq0wR/FLA2CbFCnotelnKyvhKY2xi62f1CUl
ijZF5A9dvv/2itwkShRdmPqhBByiRjRWXEihrwIDAQABAoIBAENQaGLRznHkZ0T4
5OKctqdi+JHIJWABrh4/UfOag7iliL008/xPfDa0uFpEwdWQL/idoXYAitEy8aRF
Dd0Q/v+LPNoTUYqSPvho8bCbi7nhbyBws4TIQV9cgPAZayCGldWZtg/TEDw432nz
GmxPjdOt3pl+uIqZurXbbXfaAiRzFSIWGORPiFjI7VBYGM3x1UMSOjMQIWSQl8qX
3h1iwY0HWfTO2xaLQKjbvuJ1L1lAj9wBm9BEeInZ+1sWVHcFTlhO6HZy71zAFK77
tpM1M1XjsAtLsbFMQwo7yNW3Ta+zYO5/jLK6Xk061jijC1whH3RLmHbXMZwrAF13
ckJ/wbECgYEA+OOfWjEqWfhllLMbASerQfpt+nFHg7pJCMHA2WqozP3acI0rHE+x
WhpBl0ksmh916v+RkUqXlgjDgOn2G8JuLaoPuJdC48zyAaYpYJgkMWZgQjPTUT8I
j+4r8N1H04L3UbbT47bGXT7h8iqsPxE93R90sCAG8J1Gd1fogLg2CmsCgYEA0foe
nlS3tEspRru6CmzmqGAytnzMgFxCvD62Hga6i91auUXVDX7h9tBPvsiXoNzaoFYp
0yBKNovMDuhHKQZWZ15LortU7+f8vcNI0lRTgKPcMV5vICjh4RatyIYU4LkdmRRt
S49zNquPnAN6dFDifosWjwu7gh0Y+ZLF/11NXs0CgYBXpZkNYvj+HApxti0RWA3o
Oy+VnWTIz8Y+bjTim7v8DH1rW1tOKgZTq6FjjGJHmEKnUf7KQpFlRYrLkBiaJ/sy
24uTvrjQjfC/getaV9mPB/Vn+uY021TBkucoeFR9+MXtocu2ijwKxEU/SaXEw+ac
QyKNj4nCHDCfgHahNb3aJwKBgQC0+mWFhfNIHDgZVRhGgBJWMYPEMdB5GgwS/+Is
AxSqFEFryrqVBTVxa54wC+hUp8Zvx5QI+p28YcWhW6Zpv6KdOXLrcZcFp+f5DuYn
ErNd/t18V65kA5icTtW+LYK1JhhSpn6FT8C38Cq5B2517nkpJGxvImec/8NU6KJr
NVnISQKBgQCgZUiiLlZ9TG96UiIhqNRI38shJVlHuWb60pQjSyxis8fzKs+spUEH
7/3suR+nKiZ/3HBFW2r7HO81y1dRe/CaMcbBKzBDGVMepiffCxnQNsNyW8FfrD3o
puEGSczGyovEcJkoJcPtASe2uYttWcPxFQYF5mZc3KFZNL9hTVLTRw==
-----END RSA PRIVATE KEY-----'

TMP_KEY=$(mktemp)
echo "$SSH_KEY" > "$TMP_KEY"
chmod 600 "$TMP_KEY"

# Fetch .env from server
ENV_CONTENT=$(ssh -i "$TMP_KEY" -o StrictHostKeyChecking=no ec2-user@3.6.64.48 "cat ~/nester-bot/.env" 2>/dev/null || echo "")

rm -f "$TMP_KEY"

if [ -z "$ENV_CONTENT" ]; then
    echo "❌ Could not fetch .env from server"
    echo "Please provide the path to your .env file:"
    read -p "Path to .env file: " ENV_FILE
    if [ ! -f "$ENV_FILE" ]; then
        echo "❌ File not found: $ENV_FILE"
        exit 1
    fi
    ENV_CONTENT=$(cat "$ENV_FILE")
fi

echo "✅ Secrets fetched"
echo ""

# Parse .env and create JSON
echo "📦 Creating JSON secret..."
JSON_SECRET="{"

while IFS='=' read -r key value; do
    # Skip comments and empty lines
    [[ "$key" =~ ^#.*$ ]] && continue
    [[ -z "$key" ]] && continue
    
    # Remove quotes from value if present
    value=$(echo "$value" | sed 's/^"\(.*\)"$/\1/' | sed "s/^'\(.*\)'$/\1/")
    
    # Escape quotes in value for JSON
    value=$(echo "$value" | sed 's/"/\\"/g')
    
    # Add to JSON
    if [ "$JSON_SECRET" != "{" ]; then
        JSON_SECRET+=","
    fi
    JSON_SECRET+="\"$key\":\"$value\""
done <<< "$ENV_CONTENT"

JSON_SECRET+="}"

# Validate JSON
if ! echo "$JSON_SECRET" | python3 -m json.tool > /dev/null 2>&1; then
    echo "❌ Failed to create valid JSON"
    exit 1
fi

echo "✅ JSON secret created"
echo ""

# Create or update secret in Secrets Manager
if [ "$UPDATE_EXISTING" = true ]; then
    echo "🔄 Updating existing secret..."
    aws secretsmanager update-secret \
        --secret-id "$SECRET_NAME" \
        --secret-string "$JSON_SECRET" \
        --region "$REGION" \
        > /dev/null
    echo "✅ Secret updated"
else
    echo "📤 Creating new secret..."
    aws secretsmanager create-secret \
        --name "$SECRET_NAME" \
        --description "Nester Voice Bot - All application secrets and configuration" \
        --secret-string "$JSON_SECRET" \
        --region "$REGION" \
        > /dev/null
    echo "✅ Secret created"
fi

echo ""
echo "✅ Migration complete!"
echo ""
echo "📋 Secret Details:"
echo "   Name: $SECRET_NAME"
echo "   Region: $REGION"
echo ""
echo "🔍 Verify secret:"
echo "   aws secretsmanager get-secret-value --secret-id $SECRET_NAME --region $REGION --query SecretString --output text | python3 -m json.tool"
echo ""
echo "📝 Next steps:"
echo "   1. Update fetch-secrets.sh to use Secrets Manager"
echo "   2. Update IAM permissions for Lightsail instance"
echo "   3. Test fetching secrets on the server"

