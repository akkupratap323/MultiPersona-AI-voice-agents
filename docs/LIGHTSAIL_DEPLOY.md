# AWS Lightsail Deployment Guide

Deploy NesterConversationalBot on AWS Lightsail $7/month plan.

## Prerequisites
- AWS Account
- Your `.env` file with API keys

## Step 1: Create Lightsail Instance

1. Go to https://lightsail.aws.amazon.com
2. Click **Create instance**
3. Select:
   - Region: Choose nearest to your users
   - Platform: **Linux/Unix**
   - Blueprint: **OS Only** → **Amazon Linux 2**
   - Plan: **$7/month** (1 GB RAM, 2 vCPUs, 40 GB SSD)
4. Name: `nester-voice-bot`
5. Click **Create instance**

## Step 2: Create Static IP

1. Go to **Networking** tab in Lightsail
2. Click **Create static IP**
3. Attach to your instance
4. Note your IP: `YOUR_STATIC_IP`

## Step 3: Open Firewall Ports

In Lightsail Console → Your Instance → **Networking**:

| Port | Protocol | Description |
|------|----------|-------------|
| 22   | TCP      | SSH |
| 80   | TCP      | HTTP |
| 443  | TCP      | HTTPS |
| 7860 | TCP      | FastAPI |
| 8765 | TCP      | WebSocket |

## Step 4: SSH and Setup Server

```bash
# Download SSH key from Lightsail Console → Account → SSH keys

# SSH into instance
ssh -i ~/LightsailDefaultKey.pem ec2-user@YOUR_STATIC_IP

# Update system
sudo yum update -y

# Install Docker
sudo yum install -y docker git
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

# IMPORTANT: Logout and login again for docker group
exit
# SSH back in
ssh -i ~/LightsailDefaultKey.pem ec2-user@YOUR_STATIC_IP

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker --version
docker-compose --version
```

## Step 5: Upload Project

**Option A: From your Mac (run locally)**
```bash
# Create project directory on server
ssh -i ~/LightsailDefaultKey.pem ec2-user@YOUR_STATIC_IP "mkdir -p ~/nester-bot"

# Upload files (run from project directory)
cd "/Users/apple/Desktop/nester ai bot opensource/NesterConversationalBot"

# Use rsync to upload (faster)
rsync -avz --exclude 'venv' --exclude 'node_modules' --exclude '__pycache__' \
  -e "ssh -i ~/LightsailDefaultKey.pem" \
  . ec2-user@YOUR_STATIC_IP:~/nester-bot/
```

**Option B: Git Clone**
```bash
# On the server
cd ~
git clone https://github.com/YOUR_USERNAME/NesterConversationalBot.git nester-bot
cd nester-bot
```

## Step 6: Configure Environment

```bash
# On server
cd ~/nester-bot

# Create .env file
cat > .env << 'EOF'
# API Keys
DEEPGRAM_API_KEY=your_deepgram_key
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
ELEVENLABS_VOICE_ID=your_voice_id

# LightRAG (if using)
# Update the API URL to your LightRAG server

# Server Config
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=7860
WEBSOCKET_HOST=0.0.0.0
WEBSOCKET_PORT=8765
WEBSOCKET_SERVER=websocket_server
EOF

# Edit with your actual keys
nano .env
```

## Step 7: Deploy with Docker

```bash
cd ~/nester-bot

# Build and start
docker-compose up -d --build

# Check status
docker-compose ps
docker-compose logs -f backend
```

## Step 8: Test

```bash
# Test backend
curl http://localhost:7860/status

# From your browser
http://YOUR_STATIC_IP:7860/status
http://YOUR_STATIC_IP  # Frontend
```

## Step 9: (Optional) Setup HTTPS with Caddy

```bash
# Install Caddy
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://copr.fedorainfracloud.org/coprs/caddy/caddy/repo/epel-7/caddy-caddy-epel-7.repo
sudo yum install -y caddy

# Create Caddyfile (using nip.io for free HTTPS)
sudo cat > /etc/caddy/Caddyfile << EOF
YOUR_STATIC_IP.nip.io {
    # Frontend
    handle {
        reverse_proxy localhost:80
    }
    
    # API endpoints
    handle /connect* {
        reverse_proxy localhost:7860
    }
    
    handle /status* {
        reverse_proxy localhost:7860
    }
}
EOF

# Start Caddy
sudo systemctl enable caddy
sudo systemctl start caddy
```

## Useful Commands

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart services
docker-compose restart

# Stop everything
docker-compose down

# Update deployment
git pull  # if using git
docker-compose up -d --build

# Check memory usage
free -h
docker stats
```

## Troubleshooting

### Out of Memory
If you see OOM errors, upgrade to $12/month plan (2GB RAM).

### Connection Issues
1. Check firewall ports are open
2. Check docker is running: `docker ps`
3. Check logs: `docker-compose logs backend`

### WebSocket Not Connecting
1. Ensure port 8765 is open in firewall
2. Check WebSocket URL in frontend matches server IP

## Costs

| Service | Cost |
|---------|------|
| Lightsail Instance | $7/month |
| Static IP | FREE (when attached) |
| Data Transfer | 2TB included |
| **Total** | **$7/month** |

## Your URLs

After deployment:
- Frontend: `http://YOUR_STATIC_IP/`
- API Status: `http://YOUR_STATIC_IP:7860/status`
- WebSocket: `ws://YOUR_STATIC_IP:8765`
- With HTTPS: `https://YOUR_STATIC_IP.nip.io/`

