#!/bin/bash
# Lightsail Quick Deploy Script
# Run this ON the Lightsail server after uploading files

set -e

echo "🚀 NesterConversationalBot - Lightsail Deployment"
echo "================================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Create .env file with your API keys first."
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    sudo yum install -y docker
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    echo "⚠️  Please logout and login again, then re-run this script"
    exit 0
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

echo "✅ Docker and Docker Compose ready"

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Build and start
echo "🔨 Building and starting services..."
docker-compose up -d --build

# Wait for health check
echo "⏳ Waiting for services to start..."
sleep 10

# Check status
echo ""
echo "📊 Service Status:"
docker-compose ps

# Test backend
echo ""
echo "🔍 Testing backend..."
if curl -s http://localhost:7860/status > /dev/null; then
    echo "✅ Backend is running!"
else
    echo "❌ Backend not responding"
    echo "Check logs: docker-compose logs backend"
fi

# Get public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "YOUR_IP")

echo ""
echo "================================================"
echo "🎉 Deployment Complete!"
echo "================================================"
echo ""
echo "📍 Your URLs:"
echo "   Frontend:   http://${PUBLIC_IP}/"
echo "   API:        http://${PUBLIC_IP}:7860/status"
echo "   WebSocket:  ws://${PUBLIC_IP}:7860/ws"
echo ""
echo "📝 Useful commands:"
echo "   View logs:     docker-compose logs -f"
echo "   Restart:       docker-compose restart"
echo "   Stop:          docker-compose down"
echo ""

