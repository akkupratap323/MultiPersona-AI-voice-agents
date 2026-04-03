#!/bin/bash
# Lightsail HTTPS Deploy Script
# Deploys NesterConversationalBot with automatic SSL via Caddy

set -e

echo "🔒 NesterConversationalBot - HTTPS Deployment"
echo "=============================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found!${NC}"
    echo "Create .env file with your API keys first."
    exit 1
fi

# Check for DOMAIN in .env or ask for it
if grep -q "^DOMAIN=" .env; then
    DOMAIN=$(grep "^DOMAIN=" .env | cut -d '=' -f2)
    echo -e "${GREEN}✅ Domain found: ${DOMAIN}${NC}"
else
    # Get public IP
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "")
    
    echo ""
    echo -e "${YELLOW}📝 HTTPS requires a domain name.${NC}"
    echo ""
    echo "Options:"
    echo "  1. Use your own domain (e.g., nester.yourdomain.com)"
    echo "  2. Use free nip.io subdomain (e.g., ${PUBLIC_IP}.nip.io)"
    echo ""
    read -p "Enter your domain (or press Enter for ${PUBLIC_IP}.nip.io): " INPUT_DOMAIN
    
    if [ -z "$INPUT_DOMAIN" ]; then
        if [ -z "$PUBLIC_IP" ]; then
            echo -e "${RED}❌ Could not detect public IP. Please enter domain manually.${NC}"
            exit 1
        fi
        DOMAIN="${PUBLIC_IP}.nip.io"
    else
        DOMAIN="$INPUT_DOMAIN"
    fi
    
    # Add DOMAIN to .env
    echo "" >> .env
    echo "# Domain for HTTPS" >> .env
    echo "DOMAIN=${DOMAIN}" >> .env
    echo -e "${GREEN}✅ Added DOMAIN=${DOMAIN} to .env${NC}"
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}📦 Installing Docker...${NC}"
    sudo yum install -y docker
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    echo -e "${RED}⚠️  Please logout and login again, then re-run this script${NC}"
    exit 0
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}📦 Installing Docker Compose...${NC}"
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

echo -e "${GREEN}✅ Docker and Docker Compose ready${NC}"

# Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose -f docker-compose.https.yml down 2>/dev/null || true
docker-compose down 2>/dev/null || true

# Update Caddyfile with domain
echo -e "${YELLOW}📝 Configuring Caddy for ${DOMAIN}...${NC}"
cat > Caddyfile << EOF
# Auto-generated Caddyfile for ${DOMAIN}

${DOMAIN} {
    # Frontend
    handle {
        reverse_proxy frontend:80
    }

    # API endpoints
    handle /connect* {
        reverse_proxy backend:7860
    }

    handle /status* {
        reverse_proxy backend:7860
    }

    # WebSocket
    handle /ws* {
        reverse_proxy backend:7860 {
            header_up Connection {header.Connection}
            header_up Upgrade {header.Upgrade}
        }
    }

    # Security headers
    header {
        X-Frame-Options "SAMEORIGIN"
        X-Content-Type-Options "nosniff"
        X-XSS-Protection "1; mode=block"
    }

    encode gzip
}

# HTTP redirect to HTTPS
http://${DOMAIN} {
    redir https://${DOMAIN}{uri} permanent
}
EOF

echo -e "${GREEN}✅ Caddyfile configured${NC}"

# Build and start with HTTPS compose file
echo -e "${YELLOW}🔨 Building and starting services with HTTPS...${NC}"
docker-compose -f docker-compose.https.yml up -d --build

# Wait for services
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 15

# Check status
echo ""
echo -e "${YELLOW}📊 Service Status:${NC}"
docker-compose -f docker-compose.https.yml ps

# Test backend
echo ""
echo -e "${YELLOW}🔍 Testing backend...${NC}"
if curl -s http://localhost:7860/status > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is running!${NC}"
else
    # Try through Caddy
    if curl -sk https://${DOMAIN}/status > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is running (via HTTPS)!${NC}"
    else
        echo -e "${RED}❌ Backend not responding yet (may still be starting)${NC}"
        echo "Check logs: docker-compose -f docker-compose.https.yml logs backend"
    fi
fi

# Check Caddy/SSL
echo ""
echo -e "${YELLOW}🔒 Checking SSL certificate...${NC}"
sleep 5
if curl -sI https://${DOMAIN} 2>/dev/null | grep -q "200\|301\|302"; then
    echo -e "${GREEN}✅ HTTPS is working!${NC}"
else
    echo -e "${YELLOW}⏳ SSL certificate may still be provisioning (can take 1-2 minutes)${NC}"
fi

echo ""
echo "=============================================="
echo -e "${GREEN}🎉 HTTPS Deployment Complete!${NC}"
echo "=============================================="
echo ""
echo -e "${GREEN}📍 Your Secure URLs:${NC}"
echo "   Frontend:  https://${DOMAIN}/"
echo "   API:       https://${DOMAIN}/status"
echo "   WebSocket: wss://${DOMAIN}/ws"
echo ""
echo -e "${YELLOW}📝 Useful commands:${NC}"
echo "   View logs:     docker-compose -f docker-compose.https.yml logs -f"
echo "   View Caddy:    docker-compose -f docker-compose.https.yml logs caddy"
echo "   Restart:       docker-compose -f docker-compose.https.yml restart"
echo "   Stop:          docker-compose -f docker-compose.https.yml down"
echo ""
echo -e "${YELLOW}⚠️  Note: SSL certificate provisioning may take 1-2 minutes.${NC}"
echo -e "${YELLOW}   If HTTPS doesn't work immediately, wait and try again.${NC}"
echo ""

