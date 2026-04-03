#!/bin/bash
# Script to set up GitHub secrets for NesterAIBot deployment

set -e

REPO="nesterlabs-ai/NesterAIBot"

echo "🔐 Setting up GitHub Secrets for $REPO"
echo "========================================"

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed."
    echo "Install it with: brew install gh"
    echo "Then run: gh auth login"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub CLI"
    echo "Run: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI authenticated"

# Read .env file
if [ -f .env ]; then
    echo "📄 Reading secrets from .env file..."
    source .env 2>/dev/null || true
else
    echo "⚠️  No .env file found, will use environment variables"
fi

# Set secrets function
set_secret() {
    local name=$1
    local value=$2
    if [ -n "$value" ]; then
        echo "  Setting $name..."
        echo "$value" | gh secret set "$name" -R "$REPO"
    else
        echo "  ⚠️  Skipping $name (empty)"
    fi
}

# Set secrets from file
set_secret_from_file() {
    local name=$1
    local file=$2
    if [ -f "$file" ]; then
        echo "  Setting $name from file..."
        gh secret set "$name" -R "$REPO" < "$file"
    else
        echo "  ⚠️  File not found: $file"
    fi
}

echo ""
echo "📝 Setting API Keys..."
set_secret "DEEPGRAM_API_KEY" "${DEEPGRAM_API_KEY:-}"
set_secret "GOOGLE_API_KEY" "${GOOGLE_API_KEY:-}"
set_secret "GROQ_API_KEY" "${GROQ_API_KEY:-}"
set_secret "RESEMBLE_API_KEY" "${RESEMBLE_API_KEY:-}"
set_secret "RESEMBLE_VOICE_UUID" "${RESEMBLE_VOICE_UUID:-fb2d2858}"
set_secret "LIGHTRAG_API_KEY" "${LIGHTRAG_API_KEY:-}"
set_secret "LIGHTRAG_BASE_URL" "${LIGHTRAG_BASE_URL:-}"
set_secret "PUBLIC_URL" "${PUBLIC_URL:-}"

echo ""
echo "📝 Setting Lightsail SSH credentials..."
# Look for the SSH key file
SSH_KEY_FILE=$(ls -1 "LightsailDefaultKey-ap-south-1"*.pem 2>/dev/null | head -1)
if [ -n "$SSH_KEY_FILE" ]; then
    set_secret_from_file "LIGHTSAIL_SSH_KEY" "$SSH_KEY_FILE"
else
    echo "  ⚠️  No Lightsail SSH key file found"
fi

# Set Lightsail host and user (you may need to update these)
set_secret "LIGHTSAIL_HOST" "${LIGHTSAIL_HOST:-}"
set_secret "LIGHTSAIL_USER" "${LIGHTSAIL_USER:-ec2-user}"

echo ""
echo "📝 Setting GHCR token..."
# Use GITHUB_TOKEN or prompt
if [ -n "${GHCR_TOKEN:-}" ]; then
    set_secret "GHCR_TOKEN" "$GHCR_TOKEN"
elif [ -n "${GITHUB_TOKEN:-}" ]; then
    set_secret "GHCR_TOKEN" "$GITHUB_TOKEN"
else
    echo "  ⚠️  GHCR_TOKEN not set - you may need to create a PAT"
    echo "     Go to: https://github.com/settings/tokens"
    echo "     Create token with: read:packages, write:packages, delete:packages"
fi

echo ""
echo "✅ Done! Verify secrets at:"
echo "   https://github.com/$REPO/settings/secrets/actions"
