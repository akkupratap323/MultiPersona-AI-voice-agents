#!/bin/bash
# Complete demo workflow: Start bot + ngrok in one command
# This creates two terminal tabs and starts everything

set -e

echo "🚀 NesterVoiceAI Demo Mode"
echo "=========================="
echo ""
echo "This will:"
echo "1. Start the voice bot server"
echo "2. Start ngrok tunnel for public access"
echo "3. Display your shareable URL"
echo ""

# Check if bot server is already running
if lsof -Pi :7860 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Bot is already running on port 7860"
    read -p "Do you want to stop it and restart? (y/n): " RESTART
    if [ "$RESTART" = "y" ]; then
        echo "Stopping existing server..."
        kill $(lsof -t -i:7860) 2>/dev/null || true
        sleep 2
    else
        echo "Keeping existing server running"
    fi
fi

# Check if ngrok is running
if pgrep -x "ngrok" > /dev/null; then
    echo "⚠️  ngrok is already running"
    read -p "Do you want to stop it and restart? (y/n): " RESTART_NGROK
    if [ "$RESTART_NGROK" = "y" ]; then
        echo "Stopping ngrok..."
        pkill ngrok || true
        sleep 2
    fi
fi

echo ""
echo "Starting demo mode..."
echo ""

# Detect terminal emulator and open new tabs
if [[ "$TERM_PROGRAM" == "Apple_Terminal" ]]; then
    # macOS Terminal
    osascript -e 'tell application "Terminal" to do script "cd \"'"$(pwd)"'\" && export PYTHONPATH=$(pwd) && echo \"🤖 Starting NesterVoiceAI bot...\" && python app/main.py"'
    sleep 5
    osascript -e 'tell application "Terminal" to do script "cd \"'"$(pwd)"'\" && echo \"🌐 Starting ngrok tunnel...\" && ./scripts/start-ngrok.sh"'

elif [[ "$TERM_PROGRAM" == "iTerm.app" ]]; then
    # iTerm2
    osascript -e 'tell application "iTerm" to create window with default profile command "cd \"'"$(pwd)"'\" && export PYTHONPATH=$(pwd) && python app/main.py"'
    sleep 5
    osascript -e 'tell application "iTerm" to tell current window to create tab with default profile command "cd \"'"$(pwd)"'\" && ./scripts/start-ngrok.sh"'

else
    # Fallback: Print manual instructions
    echo "⚠️  Automatic terminal tabs not supported on this terminal"
    echo ""
    echo "Please run these commands manually in separate terminals:"
    echo ""
    echo "Terminal 1:"
    echo "  cd \"$(pwd)\""
    echo "  export PYTHONPATH=\$(pwd)"
    echo "  python app/main.py"
    echo ""
    echo "Terminal 2:"
    echo "  cd \"$(pwd)\""
    echo "  ./scripts/start-ngrok.sh"
    exit 0
fi

echo "✅ Demo mode started!"
echo ""
echo "Waiting for ngrok URL (this takes ~10 seconds)..."
sleep 12

# Try to get ngrok URL from API
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o 'https://[a-zA-Z0-9.-]*\.ngrok-free\.app' | head -1)

if [ -n "$NGROK_URL" ]; then
    echo ""
    echo "════════════════════════════════════════════"
    echo "✅ Bot is live! Share this URL:"
    echo ""
    echo "   $NGROK_URL"
    echo ""
    echo "════════════════════════════════════════════"
    echo ""
    echo "Monitor traffic at: http://localhost:4040"
else
    echo ""
    echo "⚠️  Could not auto-detect ngrok URL"
    echo "Check the ngrok terminal tab for your URL"
    echo "Or visit: http://localhost:4040"
fi

echo ""
echo "To stop demo mode:"
echo "  1. Press Ctrl+C in both terminal tabs"
echo "  2. Or run: pkill -f 'python app/main.py' && pkill ngrok"
