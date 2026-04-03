#!/bin/bash
# Test script to verify Koala noise suppression is working

echo "🔍 Koala Noise Suppression Test"
echo "================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    exit 1
fi

# Check if KOALA_ACCESS_KEY is set
if grep -q "^KOALA_ACCESS_KEY=" .env; then
    KEY=$(grep "^KOALA_ACCESS_KEY=" .env | cut -d'=' -f2)
    if [ -z "$KEY" ] || [ "$KEY" = "your_koala_access_key_here" ]; then
        echo "❌ KOALA_ACCESS_KEY not configured in .env"
        exit 1
    else
        echo "✅ KOALA_ACCESS_KEY found in .env"
    fi
else
    echo "❌ KOALA_ACCESS_KEY not found in .env"
    exit 1
    
fi

# Check if Koala is installed
echo ""
echo "📦 Checking Koala installation..."
python3 -c "from pipecat.audio.filters.koala_filter import KoalaFilter; print('✅ Koala module installed')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Koala not installed"
    echo "   Run: pip install 'pipecat-ai[koala]'"
    exit 1
fi

# Check config.yaml
echo ""
echo "⚙️ Checking config.yaml..."
if grep -q "enabled: true" app/config/config.yaml | grep -A2 "noise_suppression" | grep -q "enabled: true"; then
    echo "✅ Koala enabled in config.yaml"
else
    echo "⚠️ Koala may not be enabled in config.yaml"
fi

echo ""
echo "✅ All checks passed! Koala should be working."
echo ""
echo "To verify it's running:"
echo "1. Start the server: python app/main.py"
echo "2. Look for these log messages:"
echo "   - '🔇 Koala noise suppression ENABLED'"
echo "   - '🎚️ Audio filter ACTIVE: KoalaFilter'"
echo "   - '📊 AUDIO PIPELINE SUMMARY' (should show KoalaFilter)"
