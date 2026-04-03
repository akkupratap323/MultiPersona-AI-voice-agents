#!/bin/bash
# Lightsail deployment script - GHCR pull only
# This script handles secret fetching and container deployment
# Designed to be idempotent and fail-fast

set -euo pipefail

# Configuration
DEPLOY_DIR="${DEPLOY_DIR:-/home/ec2-user/nester-bot}"
AWS_REGION="${AWS_REGION:-ap-south-1}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
GHCR_TOKEN="${GHCR_TOKEN:-}"
GHCR_USER="${GHCR_USER:-}"
PUBLIC_URL="${PUBLIC_URL:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Change to deployment directory
cd "$DEPLOY_DIR" || {
    log_error "Deployment directory not found: $DEPLOY_DIR"
    exit 1
}

log_info "=== NesterAIBot GHCR Deploy ==="
log_info "Starting deployment in: $DEPLOY_DIR"

# Port verification
log_info "🔍 Checking port 80..."
if sudo netstat -tlnp 2>/dev/null | grep -q ':80 ' || lsof -i :80 >/dev/null 2>&1; then
    log_warn "Port 80 in use, force killing..."
    sudo fuser -k 80/tcp 2>/dev/null || true
    sleep 2
fi

# Step 1: Docker login
log_info "Step 1: Authenticating with GitHub Container Registry..."
if [ -z "$GHCR_TOKEN" ] || [ -z "$GHCR_USER" ]; then
    log_error "GHCR_TOKEN or GHCR_USER not set"
    exit 1
fi

echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USER" --password-stdin || {
    log_error "Failed to login to GHCR"
    exit 1
}

# Step 2: Fetch secrets
log_info "Step 2: Fetching secrets from AWS Secrets Manager..."
if [ -f scripts/fetch-secrets.sh ]; then
    bash scripts/fetch-secrets.sh .env || {
        log_error "Failed to fetch secrets"
        exit 1
    }
else
    log_warn "fetch-secrets.sh not found, fetching directly..."
    SECRET_JSON=$(aws secretsmanager get-secret-value \
        --secret-id "nester/voice-bot/secrets" \
        --region "$AWS_REGION" \
        --query SecretString \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$SECRET_JSON" ]; then
        # Create .env from JSON using jq if available, otherwise Python
        if command -v jq &> /dev/null; then
            echo "$SECRET_JSON" | jq -r 'to_entries[] | "\(.key)=\(.value)"' > .env
        else
            TEMP_JSON=$(mktemp)
            echo "$SECRET_JSON" > "$TEMP_JSON"
            python3 -c "import json; data = json.load(open('$TEMP_JSON')); [print(f'{k}={v}') for k, v in sorted(data.items()) if v]" > .env
            rm -f "$TEMP_JSON"
        fi
        chmod 600 .env
        log_info "✅ Secrets fetched directly"
    else
        log_error "Could not fetch secrets"
        exit 1
    fi
fi

# Step 3: Update image tags in compose file
log_info "Step 3: Updating image tags..."
if [ "$IMAGE_TAG" != "latest" ]; then
    IMAGE_TAG_SHORT=$(echo "$IMAGE_TAG" | cut -c1-7)
    log_info "Using image tag: $IMAGE_TAG_SHORT"
    sed -i "s|:latest|:$IMAGE_TAG_SHORT|g" docker-compose.https.yml || {
        log_warn "Could not update image tags, using latest"
    }
else
    log_info "Using latest image tag"
fi

# Step 4: Pull images
log_info "Step 4: Pulling latest Docker images from GHCR..."
if [ ! -f docker-compose.https.yml ]; then
    log_error "docker-compose.https.yml not found"
    exit 1
fi

# Verify compose file uses image references (not build:)
if grep -q "build:" docker-compose.https.yml; then
    log_error "docker-compose.https.yml contains 'build:' sections. Use 'image:' references instead."
    exit 1
fi

export IMAGE_TAG
docker-compose -f docker-compose.https.yml pull || {
    log_error "Failed to pull Docker images"
    exit 1
}

# Step 5: Deploy containers
log_info "Step 5: Deploying containers..."

# Final port 80 cleanup
log_info "Final port 80 cleanup..."
sudo fuser -k 80/tcp 2>/dev/null || true
docker ps -q --filter "publish=80" | xargs -r docker rm -f 2>/dev/null || true

# Stop all containers including orphans
log_info "Stopping existing containers..."
docker-compose -f docker-compose.https.yml down --remove-orphans || {
    log_warn "Some containers may not have been running (this is OK)"
}

# Start containers
log_info "Starting containers..."
docker-compose -f docker-compose.https.yml up -d --remove-orphans || {
    log_error "Failed to start containers"
    log_error "Checking what's using port 80..."
    docker ps --filter "publish=80" || true
    sudo netstat -tlnp 2>/dev/null | grep ':80 ' || true
    exit 1
}

# Step 6: Wait for services
log_info "Step 6: Waiting for services to become healthy..."
sleep 15

# Check container status
log_info "Container status:"
docker-compose -f docker-compose.https.yml ps

# Step 7: Show recent logs
log_info "Step 7: Recent backend logs:"
docker logs --tail 50 nester-backend 2>&1 || log_warn "Could not fetch backend logs"

log_info "✅ Deploy complete - port 80 free"
docker ps
