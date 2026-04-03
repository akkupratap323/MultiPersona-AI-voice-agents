# Deployment Health Check Failure - Fix Required

## Issue
Backend container is failing health check during deployment with error:
```
Container nester-backend is unhealthy
dependency failed to start: container nester-backend is unhealthy
```

## Root Cause
The backend requires these environment variables to start successfully:
- `RESEMBLE_API_KEY` - For Chatterbox TTS voice synthesis
- `RESEMBLE_VOICE_UUID` - Voice ID for Resemble AI (default: 8b0c7b93)
- `LIGHTRAG_API_KEY` - For RAG system authentication (if using external LightRAG)

These variables are referenced in `docker-compose.ghcr.yml` but need to be set in the `.env` file on the Lightsail instance.

## Fix Steps

### Option 1: Add Missing Environment Variables (Recommended)

SSH into your Lightsail instance and add the missing variables to the `.env` file:

```bash
# SSH to Lightsail
ssh -i your-key.pem ubuntu@your-lightsail-ip

# Navigate to deployment directory
cd /home/ubuntu/nesterbot-ghcr

# Edit .env file
nano .env

# Add these lines:
RESEMBLE_API_KEY=lNFcgN4Qy60HcR6euolpAwtt
RESEMBLE_VOICE_UUID=8b0c7b93
LIGHTRAG_API_KEY=your_lightrag_api_key_here

# Save and exit (Ctrl+X, Y, Enter)

# Restart the deployment
docker-compose -f docker-compose.ghcr.yml down
docker-compose -f docker-compose.ghcr.yml up -d
```

### Option 2: Disable Emotion Detection (For 1GB Instance)

If you want to run without emotion detection on your 1GB instance (recommended based on our earlier analysis):

1. SSH to Lightsail instance
2. Edit `app/config/config.yaml` to disable emotion features
3. Or set environment variable to disable: `EMOTION_DETECTION_ENABLED=false`

## What Was Already Fixed

I've already pushed these fixes to GitHub:

1. ✅ Added missing environment variables to `docker-compose.ghcr.yml`:
   - `RESEMBLE_API_KEY`
   - `RESEMBLE_VOICE_UUID`
   - `LIGHTRAG_API_KEY`

2. ✅ Increased health check timeout:
   - `start_period`: 15s → 60s (allows backend initialization time)
   - `retries`: 3 → 5 (more resilient)
   - `timeout`: 10s → 15s (more time per check)

## Verification

After applying the fix, you should see:

```bash
# Check container status
docker ps

# Should show nester-backend as "healthy"
CONTAINER ID   IMAGE                                    STATUS
xxxxx          ghcr.io/.../backend:latest              Up 2 minutes (healthy)
```

## Alternative: GitHub Secrets

For production deployments, you should add these as GitHub repository secrets:

1. Go to: https://github.com/nesterlabs-ai/NesterAIBot/settings/secrets/actions
2. Add secrets:
   - `RESEMBLE_API_KEY`
   - `RESEMBLE_VOICE_UUID`
   - `LIGHTRAG_API_KEY`
3. Update `.github/workflows/deploy.yml` to pass these as environment variables

## Support

If issues persist after adding environment variables:
1. Check backend logs: `docker logs nester-backend`
2. Check if port 7860 is accessible: `curl http://localhost:7860/health`
3. Verify all dependencies are installed in the container
