#!/bin/bash
# Setup AWS Parameter Store for NesterVoiceAI Secrets
# Run this ONCE from your local machine to store secrets in AWS

set -e

echo "🔐 Setting up AWS Parameter Store for NesterVoiceAI"
echo "=================================================="

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
echo ""

# Function to store a parameter
store_param() {
    local name=$1
    local value=$2
    local desc=$3
    
    if [ -z "$value" ]; then
        echo "⚠️  Skipping $name (empty value)"
        return
    fi
    
    echo "📦 Storing: $name"
    aws ssm put-parameter \
        --name "/nester/$name" \
        --value "$value" \
        --type "SecureString" \
        --description "$desc" \
        --overwrite \
        --region ap-south-1 \
        > /dev/null 2>&1
    echo "   ✅ Done"
}

echo "Enter your API keys (they will be stored encrypted in AWS):"
echo ""

# Collect secrets interactively
read -p "DEEPGRAM_API_KEY: " DEEPGRAM_API_KEY
read -p "OPENAI_API_KEY: " OPENAI_API_KEY
read -p "GOOGLE_API_KEY (optional, press Enter to skip): " GOOGLE_API_KEY
read -p "ELEVENLABS_API_KEY: " ELEVENLABS_API_KEY
read -p "ELEVENLABS_VOICE_ID: " ELEVENLABS_VOICE_ID
read -p "PINECONE_API_KEY: " PINECONE_API_KEY
read -p "PINECONE_INDEX: " PINECONE_INDEX
read -p "PUBLIC_URL (e.g., https://3.6.64.48.nip.io): " PUBLIC_URL

echo ""
echo "📤 Uploading to AWS Parameter Store..."
echo ""

# Store each parameter
store_param "DEEPGRAM_API_KEY" "$DEEPGRAM_API_KEY" "Deepgram STT/TTS API Key"
store_param "OPENAI_API_KEY" "$OPENAI_API_KEY" "OpenAI GPT API Key"
store_param "GOOGLE_API_KEY" "$GOOGLE_API_KEY" "Google Gemini API Key"
store_param "ELEVENLABS_API_KEY" "$ELEVENLABS_API_KEY" "ElevenLabs TTS API Key"
store_param "ELEVENLABS_VOICE_ID" "$ELEVENLABS_VOICE_ID" "ElevenLabs Voice ID"
store_param "PINECONE_API_KEY" "$PINECONE_API_KEY" "Pinecone Vector DB API Key"
store_param "PINECONE_INDEX" "$PINECONE_INDEX" "Pinecone Index Name"
store_param "PUBLIC_URL" "$PUBLIC_URL" "Public URL for WebSocket"

echo ""
echo "=================================================="
echo "✅ All secrets stored in AWS Parameter Store!"
echo ""
echo "📍 Location: AWS Systems Manager > Parameter Store"
echo "🔒 Encryption: AWS KMS (default key)"
echo "🌏 Region: ap-south-1"
echo ""
echo "To view parameters:"
echo "  aws ssm get-parameters-by-path --path /nester/ --with-decryption --region ap-south-1"
echo ""

