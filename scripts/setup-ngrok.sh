#!/bin/bash
# Setup ngrok for NesterVoiceAI
# This script installs ngrok and configures it for public access

set -e

echo "🚀 NesterVoiceAI ngrok Setup"
echo "================================"

# Check if ngrok is installed
if command -v ngrok &> /dev/null; then
    echo "✅ ngrok is already installed"
    ngrok version
else
    echo "📦 Installing ngrok..."

    # Detect OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            echo "Using Homebrew to install ngrok..."
            brew install ngrok/ngrok/ngrok
        else
            echo "❌ Homebrew not found. Please install Homebrew first:"
            echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        echo "Downloading ngrok for Linux..."
        curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
            sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
            echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
            sudo tee /etc/apt/sources.list.d/ngrok.list && \
            sudo apt update && sudo apt install ngrok
    else
        echo "❌ Unsupported OS: $OSTYPE"
        echo "Please install ngrok manually from: https://ngrok.com/download"
        exit 1
    fi

    echo "✅ ngrok installed successfully"
fi

# Check if NGROK_AUTHTOKEN is set
if [ -z "$NGROK_AUTHTOKEN" ]; then
    echo ""
    echo "⚠️  NGROK_AUTHTOKEN not found in environment"
    echo ""
    echo "To get your ngrok authtoken:"
    echo "1. Sign up at: https://dashboard.ngrok.com/signup"
    echo "2. Get your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken"
    echo ""
    read -p "Enter your ngrok authtoken: " NGROK_TOKEN

    if [ -z "$NGROK_TOKEN" ]; then
        echo "❌ No authtoken provided. Exiting."
        exit 1
    fi

    # Add to .env file
    if ! grep -q "NGROK_AUTHTOKEN" .env 2>/dev/null; then
        echo "" >> .env
        echo "# ngrok configuration" >> .env
        echo "NGROK_AUTHTOKEN=$NGROK_TOKEN" >> .env
        echo "✅ Added NGROK_AUTHTOKEN to .env"
    fi

    # Configure ngrok
    ngrok config add-authtoken "$NGROK_TOKEN"
    echo "✅ ngrok authtoken configured"
else
    ngrok config add-authtoken "$NGROK_AUTHTOKEN"
    echo "✅ Using NGROK_AUTHTOKEN from environment"
fi

echo ""
echo "✅ ngrok setup complete!"
echo ""
echo "Next steps:"
echo "1. Start your bot: python app/main.py"
echo "2. In another terminal, run: ./scripts/start-ngrok.sh"
echo "3. Share the HTTPS URL with users"
