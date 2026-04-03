# AWS EC2 Deployment Guide - Nester Conversational Bot

Complete step-by-step guide to deploy your voice bot on AWS EC2 (~$15/month).

---

## Prerequisites

1. AWS Account (create at https://aws.amazon.com)
2. AWS CLI installed on your Mac
3. Your API keys ready:
   - DEEPGRAM_API_KEY
   - OPENAI_API_KEY
   - PINECONE_API_KEY (optional)

---

## Step 1: Install AWS CLI (if not installed)

```bash
# Install AWS CLI on Mac
brew install awscli

# Verify installation
aws --version
```

---

## Step 2: Configure AWS CLI

```bash
# Run configure and enter your credentials
aws configure
```

You'll be priompted for:
```
AWS Access Key ID: YOUR_ACCESS_KEY
AWS Secret Access Key: YOUR_SECRET_KEY
Default region name: us-east-1
Default output format: json
```

**To get Access Keys:**
1. Go to AWS Console → IAM → Users → Your User → Security Credentials
2. Click "Create access key"
3. Save both keys securely

---

## Step 3: Create SSH Key Pair

```bash
# Create key pair for SSH access
aws ec2 create-key-pair \
    --key-name nester-bot-key \
    --query 'KeyMaterial' \
    --output text > ~/nester-bot-key.pem

# Set correct permissions
chmod 400 ~/nester-bot-key.pem
```

---

## Step 4: Create Security Group

```bash
# Create security group
aws ec2 create-security-group \
    --group-name nester-bot-sg \
    --description "Security group for Nester Bot"

# Allow SSH (port 22)
aws ec2 authorize-security-group-ingress \
    --group-name nester-bot-sg \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0

# Allow HTTP (port 80)
aws ec2 authorize-security-group-ingress \
    --group-name nester-bot-sg \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

# Allow HTTPS (port 443)
aws ec2 authorize-security-group-ingress \
    --group-name nester-bot-sg \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0

# Allow Backend API (port 7860)
aws ec2 authorize-security-group-ingress \
    --group-name nester-bot-sg \
    --protocol tcp \
    --port 7860 \
    --cidr 0.0.0.0/0

# Allow WebSocket (port 8765)
aws ec2 authorize-security-group-ingress \
    --group-name nester-bot-sg \
    --protocol tcp \
    --port 8765 \
    --cidr 0.0.0.0/0
```

---

## Step 5: Launch EC2 Instance

```bash
# Launch t3.small instance with Amazon Linux 2023
aws ec2 run-instances \
    --image-id ami-0c7217cdde317cfec \
    --instance-type t3.small \
    --key-name nester-bot-key \
    --security-groups nester-bot-sg \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=nester-bot}]' \
    --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":20,"VolumeType":"gp3"}}]'
```

**Note:** The AMI ID `ami-0c7217cdde317cfec` is for us-east-1. For other regions, find the Amazon Linux 2023 AMI ID in the AWS Console.

---

## Step 6: Allocate Elastic IP (Free when attached)

```bash
# Allocate Elastic IP
aws ec2 allocate-address --domain vpc

# Note the AllocationId from output (e.g., eipalloc-xxxxx)

# Get your instance ID
aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=nester-bot" \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text

# Associate Elastic IP with instance (replace with your values)
aws ec2 associate-address \
    --instance-id i-YOUR_INSTANCE_ID \
    --allocation-id eipalloc-YOUR_ALLOCATION_ID
```

---

## Step 7: Get Instance Public IP

```bash
# Get the public IP address
aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=nester-bot" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text
```

Save this IP - you'll need it!

---

## Step 8: SSH into Instance

```bash
# Wait 1-2 minutes for instance to fully start, then SSH in
ssh -i ~/nester-bot-key.pem ec2-user@YOUR_PUBLIC_IP
```

---

## Step 9: Install Docker on EC2 (Run these on EC2)

```bash
# Update system
sudo yum update -y

# Install Docker
sudo yum install -y docker git

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add ec2-user to docker group (so you don't need sudo)
sudo usermod -aG docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# IMPORTANT: Log out and back in for group changes to take effect
exit
```

Then SSH back in:
```bash
ssh -i ~/nester-bot-key.pem ec2-user@YOUR_PUBLIC_IP
```

---

## Step 10: Upload Your Code to EC2

**Option A: Using SCP (from your Mac terminal, not EC2)**

```bash
# From your Mac, in the NesterConversationalBot directory
cd "/Users/apple/Desktop/nester ai bot opensource/NesterConversationalBot"

# Create a zip of the project (excluding unnecessary files)
zip -r nester-bot.zip . -x "venv/*" -x "node_modules/*" -x ".git/*" -x "__pycache__/*" -x "*.pyc"

# Upload to EC2
scp -i ~/nester-bot-key.pem nester-bot.zip ec2-user@YOUR_PUBLIC_IP:~/
```

**Option B: Using Git (if your code is on GitHub)**

```bash
# On EC2
git clone https://github.com/YOUR_USERNAME/NesterConversationalBot.git
cd NesterConversationalBot
```

---

## Step 11: Setup Project on EC2

SSH into EC2 and run:

```bash
# SSH into EC2
ssh -i ~/nester-bot-key.pem ec2-user@YOUR_PUBLIC_IP

# If you used SCP, unzip the file
cd ~
unzip nester-bot.zip -d nester-bot
cd nester-bot

# Create .env file with your API keys
cat > .env << 'EOF'
# Required API Keys
DEEPGRAM_API_KEY=your_deepgram_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Pinecone (if using RAG)
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX=voice-assistant-rag

# Server Configuration
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=7860
WEBSOCKET_HOST=0.0.0.0
WEBSOCKET_PORT=8765
WEBSOCKET_SERVER=websocket_server
SESSION_TIMEOUT=180
LOG_LEVEL=INFO
EOF

# Edit .env with your actual keys
nano .env
```

Press `Ctrl+X`, then `Y`, then `Enter` to save.

---

## Step 12: Build and Run with Docker Compose

```bash
# Make sure you're in the project directory
cd ~/nester-bot

# Build and start containers (this takes 5-10 minutes first time)
docker-compose up -d --build

# Check if containers are running
docker-compose ps

# View logs
docker-compose logs -f
```

Press `Ctrl+C` to exit logs.

---

## Step 13: Test Your Deployment

Open in your browser:
```
http://YOUR_PUBLIC_IP
```

You should see the Nester Bot frontend!

**Test the backend:**
```
http://YOUR_PUBLIC_IP:7860/status
```

---

## Step 14: Setup Auto-Start on Reboot (Optional)

```bash
# Create systemd service file
sudo tee /etc/systemd/system/nester-bot.service << 'EOF'
[Unit]
Description=Nester Bot Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ec2-user/nester-bot
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=ec2-user

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
sudo systemctl enable nester-bot.service
```

---

## Useful Commands

```bash
# View running containers
docker-compose ps

# View logs (all services)
docker-compose logs -f

# View backend logs only
docker-compose logs -f backend

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Rebuild and restart (after code changes)
docker-compose up -d --build

# Check disk space
df -h

# Check memory usage
free -m
```

---

## Updating Your Deployment

When you make code changes:

```bash
# On your Mac - create new zip
cd "/Users/apple/Desktop/nester ai bot opensource/NesterConversationalBot"
zip -r nester-bot.zip . -x "venv/*" -x "node_modules/*" -x ".git/*" -x "__pycache__/*"

# Upload to EC2
scp -i ~/nester-bot-key.pem nester-bot.zip ec2-user@YOUR_PUBLIC_IP:~/

# SSH into EC2
ssh -i ~/nester-bot-key.pem ec2-user@YOUR_PUBLIC_IP

# Backup .env, update code, restore .env
cp ~/nester-bot/.env ~/.env.backup
rm -rf ~/nester-bot
unzip ~/nester-bot.zip -d ~/nester-bot
cp ~/.env.backup ~/nester-bot/.env

# Rebuild and restart
cd ~/nester-bot
docker-compose up -d --build
```

---

## Cost Summary

| Resource | Monthly Cost |
|----------|-------------|
| EC2 t3.small | ~$15 |
| Elastic IP (attached) | Free |
| EBS Storage (20GB) | ~$2 |
| Data Transfer (first 100GB) | Free |
| **Total** | **~$17/month** |

**Save more:**
- Use t3.micro (~$8/month) if 1GB RAM is enough
- Buy Reserved Instance (1 year) for 30-40% savings

---

## Troubleshooting

### Can't SSH into instance
```bash
# Check instance is running
aws ec2 describe-instances --filters "Name=tag:Name,Values=nester-bot" --query 'Reservations[0].Instances[0].State.Name'

# Check security group has port 22 open
aws ec2 describe-security-groups --group-names nester-bot-sg
```

### Docker containers not starting
```bash
# Check Docker is running
sudo systemctl status docker

# Check container logs
docker-compose logs
```

### Out of memory
```bash
# Check memory
free -m

# If low, upgrade to t3.small or t3.medium
```

### Website not loading
```bash
# Check containers are running
docker-compose ps

# Check security group allows port 80
aws ec2 describe-security-groups --group-names nester-bot-sg
```

---

## Quick Reference

```bash
# SSH into your server
ssh -i ~/nester-bot-key.pem ec2-user@YOUR_PUBLIC_IP

# Your app URL
http://YOUR_PUBLIC_IP

# Backend status
http://YOUR_PUBLIC_IP:7860/status
```

Replace `YOUR_PUBLIC_IP` with your actual Elastic IP address.
