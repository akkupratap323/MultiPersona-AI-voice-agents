#!/bin/bash
# =============================================================================
# Verify Code Version and Fix if Using Old Code
# =============================================================================
# This script checks if the server is using the latest code by comparing
# the container's image tag with the latest commit SHA from GitHub.
# If old code is detected, it recreates the container with the latest image.
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_debug() { echo -e "${CYAN}[DEBUG]${NC} $1"; }

echo "=========================================="
echo "🔍 CODE VERSION VERIFICATION & FIX"
echo "=========================================="
echo ""

# Step 1: Get current container image
log_info "Step 1: Checking current container image..."
CURRENT_IMAGE=$(docker inspect nester-backend 2>/dev/null | grep -oP '"Image":\s*"\K[^"]+' | head -1 || echo "")

if [ -z "$CURRENT_IMAGE" ]; then
    log_error "❌ Could not get current container image. Is nester-backend running?"
    exit 1
fi

log_info "Current image: $CURRENT_IMAGE"
echo ""

# Step 2: Extract commit SHA from image tag
CURRENT_SHA=""
if echo "$CURRENT_IMAGE" | grep -qE ":[a-f0-9]{7,}"; then
    CURRENT_SHA=$(echo "$CURRENT_IMAGE" | grep -oE ":[a-f0-9]{7,}" | cut -d: -f2 | head -1)
    log_info "Current commit SHA in image: $CURRENT_SHA"
elif echo "$CURRENT_IMAGE" | grep -q ":latest"; then
    log_warn "⚠️  Container is using 'latest' tag - cannot verify exact version"
    CURRENT_SHA="latest"
else
    log_warn "⚠️  Could not extract commit SHA from image tag"
fi
echo ""

# Step 3: Get latest commit SHA from GitHub
log_info "Step 2: Fetching latest commit SHA from GitHub..."
REPO_URL="${GITHUB_REPO:-https://github.com/nesterlabs-ai/NesterAIBot.git}"
LATEST_SHA=""

# Try to get latest commit SHA
if command -v git &> /dev/null; then
    # If we're in a git repo, get the latest from origin
    if [ -d .git ]; then
        git fetch origin main 2>/dev/null || true
        LATEST_SHA=$(git rev-parse origin/main 2>/dev/null | cut -c1-7 || echo "")
    fi
fi

# Fallback: Use GitHub API
if [ -z "$LATEST_SHA" ]; then
    log_debug "Trying GitHub API to get latest commit..."
    LATEST_SHA=$(curl -s "https://api.github.com/repos/nesterlabs-ai/NesterAIBot/commits/main" | grep -oP '"sha":\s*"\K[a-f0-9]+' | head -1 | cut -c1-7 || echo "")
fi

if [ -z "$LATEST_SHA" ]; then
    log_warn "⚠️  Could not fetch latest commit SHA. Will check image digest instead."
    USE_DIGEST_CHECK=true
else
    log_info "Latest commit SHA (main branch): $LATEST_SHA"
    USE_DIGEST_CHECK=false
fi
echo ""

# Step 4: Compare versions
log_info "Step 3: Comparing versions..."
NEEDS_UPDATE=false

if [ "$USE_DIGEST_CHECK" = false ]; then
    if [ "$CURRENT_SHA" = "latest" ]; then
        log_warn "⚠️  Using 'latest' tag - cannot verify if it's the newest"
        log_info "Checking if we need to pull latest image..."
        NEEDS_UPDATE=true
    elif [ "$CURRENT_SHA" != "$LATEST_SHA" ]; then
        log_warn "⚠️  VERSION MISMATCH DETECTED!"
        log_warn "   Current: $CURRENT_SHA"
        log_warn "   Latest:  $LATEST_SHA"
        NEEDS_UPDATE=true
    else
        log_info "✅ Container is using the latest code (commit $CURRENT_SHA)"
    fi
else
    # Fallback: Check if image needs to be pulled
    log_info "Checking if latest image is available..."
    NEEDS_UPDATE=true
fi
echo ""

# Step 5: Check container logs for code version indicators
log_info "Step 4: Checking container logs for code version indicators..."
echo "--- Recent startup logs (last 30 lines) ---"
docker logs --tail 30 nester-backend 2>&1 | grep -E "Starting|Initialized|version|commit|sha" || echo "No version indicators found"
echo ""

# Step 6: Fix if needed
if [ "$NEEDS_UPDATE" = true ]; then
    log_warn "⚠️  Container may be using old code. Recreating with latest image..."
    echo ""
    
    # Check if docker-compose.https.yml exists
    if [ ! -f docker-compose.https.yml ]; then
        log_error "❌ docker-compose.https.yml not found!"
        exit 1
    fi
    
    # Login to GHCR if needed
    if [ -n "${GHCR_TOKEN:-}" ] && [ -n "${GHCR_USER:-}" ]; then
        log_info "Logging into GHCR..."
        echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USER" --password-stdin || {
            log_warn "⚠️  GHCR login failed, but continuing..."
        }
    fi
    
    # Pull latest images
    log_info "Pulling latest images..."
    docker-compose -f docker-compose.https.yml pull || {
        log_warn "⚠️  Pull failed, but continuing with recreate..."
    }
    
    # Force recreate container
    log_info "Recreating backend container..."
    docker-compose -f docker-compose.https.yml up -d --force-recreate --no-deps backend || {
        log_error "❌ Failed to recreate container"
        exit 1
    }
    
    log_info "⏳ Waiting for container to start..."
    sleep 15
    
    # Verify new container
    log_info "Verifying new container..."
    NEW_IMAGE=$(docker inspect nester-backend 2>/dev/null | grep -oP '"Image":\s*"\K[^"]+' | head -1 || echo "")
    log_info "New image: $NEW_IMAGE"
    
    # Check container health
    if docker ps | grep -q "nester-backend.*healthy"; then
        log_info "✅ Container is healthy"
    elif docker ps | grep -q "nester-backend"; then
        log_warn "⚠️  Container is running but not yet healthy"
        log_info "Check logs: docker logs nester-backend"
    else
        log_error "❌ Container failed to start"
        docker logs --tail 50 nester-backend 2>&1 || true
        exit 1
    fi
    
    echo ""
    log_info "✅ Container recreated successfully!"
else
    log_info "✅ No update needed - container is using latest code"
fi

echo ""
echo "=========================================="
echo "📋 FINAL STATUS"
echo "=========================================="
docker ps --filter "name=nester-backend" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
echo ""
log_info "To view logs: docker logs -f nester-backend"
log_info "To check health: curl http://localhost:7860/health"
echo ""

