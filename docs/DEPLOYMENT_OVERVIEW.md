# NesterConversationalBot - Deployment Overview

> A practical guide to our AWS Lightsail deployment: tools, setup, costs, and recommendations.

---

## 🛠️ Deployment Tools & Why We Need Them

### Infrastructure Tools

| Tool | Purpose | Why We Chose It |
|------|---------|-----------------|
| **AWS Lightsail** | Cloud hosting | Fixed $7/month pricing, simple management, 2TB bandwidth included |
| **Docker** | Containerization | Consistent environment across dev/prod, easy deployment |
| **Docker Compose** | Multi-container orchestration | Single command to start all services |
| **Caddy** | Reverse proxy + SSL | Auto HTTPS with Let's Encrypt, zero-config SSL |

### Application Stack

| Tool | Purpose | Why We Chose It |
|------|---------|-----------------|
| **Python 3.11** | Backend runtime | Async support, rich AI/ML ecosystem |
| **FastAPI** | Web framework | Fast, async, WebSocket support, auto-docs |
| **Pipecat** | Voice AI framework | Real-time audio streaming, provider-agnostic |
| **Nginx** | Static file server | Lightweight, efficient, production-ready |

### External APIs

| Service | Purpose | Cost Model |
|---------|---------|------------|
| **Deepgram** | Speech-to-Text & Text-to-Speech | Pay-per-minute (~$0.0043/min STT, $0.015/1K chars TTS) |
| **OpenAI** | LLM (GPT-3.5 Turbo) | Pay-per-token (~$0.002/1K tokens) |
| **LightRAG** | Knowledge retrieval | Self-hosted (no cost) |

---

## 🚀 How We Set Up the Deployment

### Step 1: Create Lightsail Instance (2 min)

```
AWS Console → Lightsail → Create Instance
├── Region: ap-south-1 (Mumbai)
├── OS: Amazon Linux 2023
├── Plan: $7/month (1GB RAM, 2 vCPU, 40GB SSD)
└── Name: nester-voice-bot
```

### Step 2: Configure Networking (2 min)

```
Lightsail Console → Networking
├── Create Static IP → Attach to instance (FREE)
└── Open Firewall Ports: 22, 80, 443, 7860, 8765
```

### Step 3: Install Docker (5 min)

```bash
# SSH into instance
ssh -i ~/LightsailKey.pem ec2-user@YOUR_IP

# Install Docker
sudo yum install -y docker git
sudo systemctl start docker && sudo systemctl enable docker
sudo usermod -aG docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Step 4: Upload & Deploy (5 min)

```bash
# Upload project
rsync -avz --exclude 'venv' --exclude 'node_modules' . ec2-user@YOUR_IP:~/nester-bot/

# Deploy
cd ~/nester-bot
cp env.example .env  # Edit with your API keys
docker-compose up -d --build
```

### Step 5: Setup HTTPS with Caddy (5 min)

```bash
# Install Caddy
sudo yum install -y caddy

# Configure (auto SSL with nip.io)
sudo tee /etc/caddy/Caddyfile << EOF
YOUR_IP.nip.io {
    handle /connect* { reverse_proxy localhost:7860 }
    handle /status* { reverse_proxy localhost:7860 }
    handle /ws { reverse_proxy localhost:8765 }
    handle { 
        root * /var/www/nester
        try_files {path} /index.html
        file_server
    }
}
EOF

# Start Caddy
sudo systemctl enable caddy && sudo systemctl start caddy
```

**Total Setup Time: ~20 minutes**

---

## 💰 Economic Analysis

### Monthly Infrastructure Cost

| Component | Cost |
|-----------|------|
| Lightsail Instance (1GB) | $7.00 |
| Static IP | FREE (when attached) |
| Data Transfer (2TB) | INCLUDED |
| Storage (40GB SSD) | INCLUDED |
| SSL Certificate | FREE (Let's Encrypt) |
| **Total Infrastructure** | **$7.00/month** |

### Estimated API Costs (Moderate Usage: ~100 conversations/day)

| Service | Usage Estimate | Monthly Cost |
|---------|----------------|--------------|
| Deepgram STT | ~50 min/day | ~$6.50 |
| Deepgram TTS | ~100K chars/day | ~$4.50 |
| OpenAI GPT-3.5 | ~500K tokens/day | ~$3.00 |
| **Total API** | | **~$14/month** |

### Total Monthly Cost: **~$21/month**

### Comparison with Alternatives

| Platform | Monthly Cost | Notes |
|----------|--------------|-------|
| **Our Setup (Lightsail)** | **~$21** | Full control, scalable |
| AWS EC2 equivalent | ~$35-50 | Variable pricing, complex |
| Heroku | ~$50-75 | Easy but expensive |
| Managed Voice AI (Bland.ai, etc.) | ~$100-500 | Less customization |

**Savings: 50-90%** compared to alternatives!

---

## ✅ What's Good About This Deployment

### Strengths

| Aspect | Rating | Why |
|--------|--------|-----|
| **Cost Efficiency** | ⭐⭐⭐⭐⭐ | $7/month infrastructure |
| **Simplicity** | ⭐⭐⭐⭐ | Docker Compose = 1 command deploy |
| **SSL/HTTPS** | ⭐⭐⭐⭐⭐ | Auto SSL with Caddy |
| **Scalability** | ⭐⭐⭐ | Good for 10-20 concurrent users |
| **Reliability** | ⭐⭐⭐⭐ | AWS infrastructure |
| **Maintainability** | ⭐⭐⭐⭐ | Simple architecture |

### Current Capacity

- **Concurrent Users:** ~10-15
- **Response Time:** < 2 seconds voice-to-voice
- **Uptime:** 99.9%+ (AWS SLA)

---

## 🔧 What Could Be Improved

### For Better Performance

| Improvement | Effort | Impact |
|-------------|--------|--------|
| Upgrade to $12 plan (2GB RAM) | Low | Handle more concurrent users |
| Add Redis for session caching | Medium | Faster response times |
| Use WebSocket load balancing | High | Scale to 100+ users |

### For Better Reliability

| Improvement | Effort | Impact |
|-------------|--------|--------|
| Add health monitoring (CloudWatch) | Low | Early problem detection |
| Setup automated backups | Low | Data protection |
| Add CI/CD pipeline | Medium | Faster, safer deployments |

### For Production Scale (100+ users)

| Improvement | Estimated Cost |
|-------------|----------------|
| Upgrade to $24 plan (4GB RAM) | +$17/month |
| Add Load Balancer | +$18/month |
| Multiple instances (2-3) | +$14-21/month |
| **Total for scale** | ~$60-80/month |

---

## 📊 Deployment Architecture

```
                    Internet
                        │
                        ▼
              ┌─────────────────┐
              │   Caddy Proxy   │  ← Auto SSL (Let's Encrypt)
              │   (Port 80/443) │
              └────────┬────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
    ┌─────────┐  ┌──────────┐  ┌──────────┐
    │ Static  │  │ FastAPI  │  │WebSocket │
    │ Files   │  │  :7860   │  │  :8765   │
    └─────────┘  └──────────┘  └──────────┘
         │             │             │
         └─────────────┴─────────────┘
                       │
              Docker Container
              (nester-backend)
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
    ┌─────────┐  ┌──────────┐  ┌──────────┐
    │Deepgram │  │  OpenAI  │  │ LightRAG │
    │STT/TTS  │  │GPT-3.5   │  │   API    │
    └─────────┘  └──────────┘  └──────────┘
```

---

## 🎯 Recommendations

### For Startups/Small Scale (Current Setup) ✅

**Verdict: Perfect fit!**
- Cost: ~$21/month
- Capacity: 10-15 concurrent users
- Maintenance: Minimal

### For Medium Scale (50-100 users)

**Recommendation: Upgrade plan + add monitoring**
- Cost: ~$40-50/month
- Changes needed:
  - Upgrade to $24 Lightsail plan
  - Add CloudWatch monitoring
  - Setup automated backups

### For Large Scale (100+ users)

**Recommendation: Move to ECS/Kubernetes**
- Cost: $100-300/month
- Changes needed:
  - Multiple containers with load balancer
  - Auto-scaling
  - Managed database for sessions

---

## 📝 Quick Commands Reference

```bash
# Deploy
docker-compose up -d --build

# View logs
docker-compose logs -f backend

# Restart
docker-compose restart backend

# Update code
rsync -avz --exclude 'venv' . ec2-user@IP:~/nester-bot/
ssh ec2-user@IP "cd ~/nester-bot && docker-compose up -d --build"

# Check status
curl https://YOUR_IP.nip.io/status
```

---

## ✅ Conclusion

This deployment is **excellent for normal scale** (startups, demos, small businesses):

| Criteria | Assessment |
|----------|------------|
| **Cost** | 🟢 Very affordable ($7-21/month) |
| **Setup** | 🟢 Simple (~20 min) |
| **Maintenance** | 🟢 Minimal effort |
| **Performance** | 🟢 Good for 10-15 users |
| **Scalability** | 🟡 Needs upgrades for 50+ users |
| **Production-ready** | 🟢 Yes, with HTTPS |

**Bottom line:** This is a production-ready, cost-effective deployment suitable for most use cases. Scale up only when you actually need it!

---

*Last Updated: December 2024*

