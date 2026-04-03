#!/bin/bash
# Setup script for Koala noise suppression

set -e

echo "🔇 Koala Noise Suppression Setup"
echo "================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
fi

# Koala access key
KOALA_KEY="cPT0VLUHzN4ScG9Jw+CcEsNvM/Wjvdetge+jgswMrj+iheYN6LWmkg=="

# Check if key already exists in .env
if grep -q "^KOALA_ACCESS_KEY=" .env; then
    # Update existing key
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|^KOALA_ACCESS_KEY=.*|KOALA_ACCESS_KEY=${KOALA_KEY}|" .env
    else
        # Linux
        sed -i "s|^KOALA_ACCESS_KEY=.*|KOALA_ACCESS_KEY=${KOALA_KEY}|" .env
    fi
    echo "✅ Updated KOALA_ACCESS_KEY in .env"
else
    # Add new key
    echo "" >> .env
    echo "# Koala Noise Suppression" >> .env
    echo "KOALA_ACCESS_KEY=${KOALA_KEY}" >> .env
    echo "✅ Added KOALA_ACCESS_KEY to .env"
fi

echo ""
echo "📦 Installing Koala dependencies..."
pip install "pipecat-ai[koala]"

echo ""
echo "✅ Koala noise suppression is now configured!"
echo ""
echo "To verify it's working, check the logs when starting the server:"
echo "  python app/main.py"
echo ""
echo "You should see: '🔇 Koala noise suppression ENABLED'"
