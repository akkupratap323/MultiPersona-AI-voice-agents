#!/bin/bash
# =============================================================================
# Install and Configure AWS CloudWatch Agent for Docker Logs
# =============================================================================
# This script installs the CloudWatch agent on Lightsail/EC2 instances
# and configures it to collect Docker container logs
# =============================================================================

set -euo pipefail

REGION="${AWS_REGION:-ap-south-1}"
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null || echo "lightsail-instance")
CONFIG_FILE="/opt/aws/amazon-cloudwatch-agent/bin/config.json"

echo "=========================================="
echo "CloudWatch Agent Installation & Setup"
echo "=========================================="
echo "Region: $REGION"
echo "Instance ID: $INSTANCE_ID"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Step 1: Download CloudWatch Agent
echo "📥 Step 1: Downloading CloudWatch Agent..."
cd /tmp
if [ ! -f "amazon-cloudwatch-agent.deb" ]; then
    wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
    echo "✅ Download complete"
else
    echo "✅ Agent already downloaded"
fi

# Step 2: Install CloudWatch Agent
echo ""
echo "📦 Step 2: Installing CloudWatch Agent..."
if ! dpkg -l | grep -q amazon-cloudwatch-agent; then
    sudo dpkg -i -E ./amazon-cloudwatch-agent.deb
    echo "✅ Installation complete"
else
    echo "✅ Agent already installed"
fi

# Step 3: Create CloudWatch Log Groups
echo ""
echo "📝 Step 3: Creating CloudWatch Log Groups..."
aws logs create-log-group \
    --log-group-name "/lightsail/nester-docker" \
    --region "$REGION" \
    2>/dev/null && echo "✅ Created /lightsail/nester-docker" || echo "⚠️  Log group may already exist"

aws logs create-log-group \
    --log-group-name "/lightsail/nester-system" \
    --region "$REGION" \
    2>/dev/null && echo "✅ Created /lightsail/nester-system" || echo "⚠️  Log group may already exist"

# Set retention to 30 days
aws logs put-retention-policy \
    --log-group-name "/lightsail/nester-docker" \
    --retention-in-days 30 \
    --region "$REGION" \
    2>/dev/null || true

aws logs put-retention-policy \
    --log-group-name "/lightsail/nester-system" \
    --retention-in-days 30 \
    --region "$REGION" \
    2>/dev/null || true

# Step 4: Copy configuration file
echo ""
echo "⚙️  Step 4: Configuring CloudWatch Agent..."
if [ -f "/home/ec2-user/nester-bot/scripts/cloudwatch-agent-config.json" ]; then
    cp /home/ec2-user/nester-bot/scripts/cloudwatch-agent-config.json "$CONFIG_FILE"
    echo "✅ Configuration file copied"
elif [ -f "./scripts/cloudwatch-agent-config.json" ]; then
    cp ./scripts/cloudwatch-agent-config.json "$CONFIG_FILE"
    echo "✅ Configuration file copied"
else
    echo "⚠️  Configuration file not found, using default config"
    # Create basic config if file doesn't exist
    cat > "$CONFIG_FILE" << 'EOF'
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/lib/docker/containers/*/*-json.log",
            "log_group_name": "/lightsail/nester-docker",
            "log_stream_name": "{instance_id}-{container_name}",
            "timezone": "UTC",
            "encoding": "utf-8"
          }
        ]
      }
    }
  }
}
EOF
fi

# Step 5: Start CloudWatch Agent
echo ""
echo "🚀 Step 5: Starting CloudWatch Agent..."
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -c file:$CONFIG_FILE \
    -s

echo ""
echo "=========================================="
echo "✅ CloudWatch Agent Setup Complete!"
echo "=========================================="
echo ""
echo "Log Groups:"
echo "  - /lightsail/nester-docker (Docker container logs)"
echo "  - /lightsail/nester-system (System logs)"
echo ""
echo "To check agent status:"
echo "  sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -m ec2 -a status"
echo ""
echo "To view logs in CloudWatch:"
echo "  aws logs tail /lightsail/nester-docker --follow --region $REGION"
echo ""
echo "To view logs in CloudWatch Console:"
echo "  https://console.aws.amazon.com/cloudwatch/home?region=$REGION#logsV2:log-groups"
echo ""

