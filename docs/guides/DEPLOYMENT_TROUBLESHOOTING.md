# Deployment Troubleshooting Guide

## Common Deployment Issues & Solutions

### Issue 1: Backend Container Unhealthy (SOLVED)

#### **Symptoms:**
```
Container nester-backend is unhealthy
dependency failed to start: container nester-backend is unhealthy
```

#### **Root Cause:**
After restructuring the project and adding LLM-based sentiment detection, the backend container was failing health checks because:

1. **Application startup time increased** (~30-45 seconds)
   - Groq/Llama LLM client initialization
   - MSP-PODCAST emotion detector loading
   - Model downloads and setup
   - Configuration and service connections

2. **Health check started too early**
   - Original: `start_period=5s` (too short!)
   - Application wasn't ready when health check ran
   - Container marked as unhealthy before it finished starting

3. **Missing environment variable**
   - `GROQ_API_KEY` not in `docker-compose.https.yml`
   - Caused LLM initialization to fail
   - Application couldn't start properly

4. **Caddyfile path incorrect**
   - Path: `./Caddyfile` (old location)
   - After restructuring: `./deployment/docker/Caddyfile`
   - Caddy couldn't find reverse proxy configuration

#### **Solution Applied:**

**1. Extended Health Check Timing** (`deployment/docker/Dockerfile`):
```dockerfile
# Before
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3

# After
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=5
```

**2. Added Missing Environment Variable** (`docker-compose.https.yml`):
```yaml
environment:
  - GROQ_API_KEY=${GROQ_API_KEY}  # Added this line
```

**3. Fixed Caddyfile Path** (`docker-compose.https.yml`):
```yaml
volumes:
  - ./deployment/docker/Caddyfile:/etc/caddy/Caddyfile:ro  # Updated path
```

#### **Why This Works:**

- **60-second start period**: Gives application time to:
  - Load all Python dependencies
  - Initialize Groq LLM client
  - Load MSP-PODCAST model
  - Connect to external services
  - Start FastAPI server on port 7860

- **5 retries with 30s intervals**:
  - Total grace period: 60s + (5 × 30s) = 210 seconds
  - Plenty of time for slower starts on production servers

- **GROQ_API_KEY**:
  - Allows LLM text sentiment to initialize properly
  - Prevents application startup errors

### Issue 2: Cascade Failure Pattern

#### **Problem:**
When backend fails, everything else fails in sequence:

```
Backend unhealthy
    ↓
Caddy can't start (depends_on: backend healthy)
    ↓
Frontend can't start (depends_on: backend healthy)
    ↓
Entire deployment fails
```

#### **Solution:**
Fix the root cause (backend health check) and all dependent services will start automatically.

### Issue 3: Port 80 Conflicts

#### **Symptoms:**
```
Error: Port 80 is already in use
```

#### **Solution:**
The deployment script automatically handles this:
```bash
sudo fuser -k 80/tcp 2>/dev/null || true
docker ps -q --filter "publish=80" | xargs -r docker rm -f
```

### Health Check Best Practices

#### **For Development:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3
```
- Fast startup for development iteration

#### **For Production with LLM/AI Models:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=5
```
- Accounts for model loading time
- More retries for reliability
- Longer timeout for slower servers

### Debugging Health Check Failures

#### **1. Check Container Logs:**
```bash
docker logs nester-backend --tail 100
```

Look for:
- `Uvicorn running on http://0.0.0.0:7860`
- `Application startup complete`
- Any errors or exceptions

#### **2. Manual Health Check:**
```bash
# Inside container
docker exec nester-backend curl -f http://localhost:7860/health

# From host
curl http://localhost:7860/health
```

Expected response:
```json
{"status": "healthy"}
```

#### **3. Check Health Status:**
```bash
docker ps
# Look at the STATUS column - should show "healthy"
```

#### **4. Inspect Health Check Results:**
```bash
docker inspect nester-backend | grep -A 10 "Health"
```

### Environment Variables Checklist

Ensure these are set in production `.env` or secrets manager:

**Required for Basic Functionality:**
- ✅ `DEEPGRAM_API_KEY` - Speech-to-Text
- ✅ `GOOGLE_API_KEY` - LLM (if using Gemini)
- ✅ `GROQ_API_KEY` - **NEW:** LLM for text sentiment
- ✅ `PUBLIC_URL` - Frontend WebSocket connection

**Optional but Recommended:**
- `RESEMBLE_API_KEY` - Enhanced TTS
- `RESEMBLE_VOICE_UUID` - Voice selection
- `LIGHTRAG_API_KEY` - RAG system
- `LIGHTRAG_BASE_URL` - RAG endpoint

### Startup Timing Analysis

**Local Development (M1 Mac):**
- Application startup: ~5-8 seconds
- Health check passes: ~10 seconds

**Production (AWS Lightsail t3.small):**
- Application startup: ~20-45 seconds
- Health check passes: ~60 seconds
- Factors: CPU speed, model downloads, network latency

### Common Errors & Quick Fixes

#### **Error: "curl: command not found"**
```dockerfile
# Add to Dockerfile
RUN apt-get install -y curl
```

#### **Error: "Connection refused"**
- Application hasn't started yet
- Check if port 7860 is actually listening
- Increase `start_period` in health check

#### **Error: "Service unhealthy"**
- Check application logs for startup errors
- Verify all required environment variables are set
- Ensure `/health` endpoint is implemented

### Testing Deployment Locally

Before pushing to production:

```bash
# 1. Build images
make docker-build

# 2. Start with compose
docker-compose -f deployment/docker/docker-compose.yml up

# 3. Watch logs
docker logs -f nester-backend

# 4. Check health
curl http://localhost:7860/health

# 5. Verify WebSocket
# Open http://localhost in browser
```

### GitHub Actions CI/CD

After fixes are pushed, the deployment pipeline will:

1. ✅ Build backend image with new Dockerfile
2. ✅ Build frontend image
3. ✅ Push to GHCR
4. ✅ Deploy to Lightsail
5. ✅ Health check passes (60s grace period)
6. ✅ Caddy starts (backend is healthy)
7. ✅ Frontend starts (backend is healthy)
8. ✅ Deployment complete

### Monitoring Deployment

**Watch GitHub Actions:**
```
https://github.com/nesterlabs-ai/NesterAIBot/actions
```

**Check Lightsail Logs:**
```bash
ssh ubuntu@<lightsail-ip>
cd ~/nester-bot
docker-compose -f docker-compose.https.yml logs -f backend
```

**Verify Services Running:**
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
```

Expected output:
```
NAMES             STATUS                    IMAGE
nester-backend    Up 2 minutes (healthy)    ghcr.io/nesterlabs-ai/nesteraibot-backend:latest
nester-frontend   Up 2 minutes              ghcr.io/nesterlabs-ai/nesteraibot-frontend:latest
nester-caddy      Up 2 minutes              caddy:2-alpine
```

### Summary

**Key Fixes Applied:**
1. ✅ Increased health check start period (5s → 60s)
2. ✅ Added GROQ_API_KEY to environment
3. ✅ Fixed Caddyfile path for restructured project
4. ✅ Increased timeout and retries for reliability

**Result:**
- Backend starts successfully
- Health check passes
- Caddy starts (depends on healthy backend)
- Frontend starts (depends on healthy backend)
- ✅ Deployment succeeds

---

**Last Updated:** January 14, 2026
**Status:** Resolved
**Commit:** 532238a
