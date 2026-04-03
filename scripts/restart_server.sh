#!/bin/bash

# Restart Script for Nester AI Voice Assistant
# This script stops any running instances and starts the server fresh

echo "🔄 Restarting Nester AI Voice Assistant Server..."
echo "================================================"

# Stop any running instances
echo "⏹️  Stopping existing server instances..."
pkill -f "uvicorn app.main:app" || echo "No running instances found"
pkill -f "python.*app/main.py" || true
sleep 2

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "⚠️  No virtual environment found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
else
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
fi

echo "✅ Virtual environment activated"

# Clear Python cache
echo "🧹 Clearing Python cache..."
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Export environment variables
export PYTHONUNBUFFERED=1

# Start server with logs
echo ""
echo "🚀 Starting server on http://0.0.0.0:7860"
echo "📊 WebSocket endpoint: ws://0.0.0.0:7860/ws"
echo "================================================"
echo ""
echo "🔍 HYBRID MODE ENABLED - Watch for these log patterns:"
echo "  🔄 'HYBRID MODE: Processing audio + text'"
echo "  🎯 'HYBRID RESULT: Primary Emotion...'"
echo "  Audio: emotion × weight%"
echo "  Text:  emotion × weight%"
echo "  Mismatch: true/false"
echo ""
echo "📝 Logs starting..."
echo "================================================"
echo ""

# Run server with colored output
python3 -u -m uvicorn app.main:app --host 0.0.0.0 --port 7860 --reload 2>&1 | while IFS= read -r line; do
    # Add timestamp to each line
    echo "[$(date '+%H:%M:%S')] $line"
done
