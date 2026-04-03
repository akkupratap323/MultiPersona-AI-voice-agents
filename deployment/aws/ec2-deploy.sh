#!/bin/bash
# Budget-Friendly EC2 Deployment Script
# Estimated Cost: $8-15/month (t3.micro/small)

set -e

# Configuration
AWS_REGION="us-east-1"
INSTANCE_TYPE="t3.small"  # t3.micro for absolute minimum ($8/mo)
KEY_NAME="nester-key"     # Your SSH key name
AMI_ID="ami-0c7217cdde317cfec"  # Amazon Linux 2023 (us-east-1, update for your region)

echo "=========================================="
echo "  Budget EC2 Deployment for Nester Bot"
echo "=========================================="

# Create security group
echo "Creating security group..."
SG_ID=$(aws ec2 create-security-group \
    --group-name nester-sg \
    --description "Nester Bot Security Group" \
    --region $AWS_REGION \
    --query 'GroupId' --output text 2>/dev/null || \
    aws ec2 describe-security-groups \
    --group-names nester-sg \
    --region $AWS_REGION \
    --query 'SecurityGroups[0].GroupId' --output text)

# Add security group rules
echo "Configuring security group rules..."
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 22 --cidr 0.0.0.0/0 --region $AWS_REGION 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 80 --cidr 0.0.0.0/0 --region $AWS_REGION 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 443 --cidr 0.0.0.0/0 --region $AWS_REGION 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 7860 --cidr 0.0.0.0/0 --region $AWS_REGION 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8765 --cidr 0.0.0.0/0 --region $AWS_REGION 2>/dev/null || true

# User data script to install Docker and run the app
USER_DATA=$(cat << 'USERDATA'
#!/bin/bash
yum update -y
yum install -y docker git
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install docker-compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Clone and setup (update with your repo)
cd /home/ec2-user
# git clone https://github.com/YOUR_REPO/NesterConversationalBot.git
# cd NesterConversationalBot

# Create .env file (secrets should be passed via SSM Parameter Store in production)
# echo "DEEPGRAM_API_KEY=xxx" >> .env
# echo "OPENAI_API_KEY=xxx" >> .env

# Start the application
# docker-compose up -d

echo "Setup complete! SSH in and configure your .env file, then run docker-compose up -d"
USERDATA
)

# Launch EC2 instance
echo "Launching EC2 instance ($INSTANCE_TYPE)..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SG_ID \
    --user-data "$USER_DATA" \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=nester-bot}]' \
    --region $AWS_REGION \
    --query 'Instances[0].InstanceId' --output text)

echo "Instance ID: $INSTANCE_ID"

# Wait for instance to be running
echo "Waiting for instance to start..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $AWS_REGION

# Allocate and associate Elastic IP (free when attached to running instance)
echo "Allocating Elastic IP..."
ALLOC_ID=$(aws ec2 allocate-address --domain vpc --region $AWS_REGION --query 'AllocationId' --output text)
aws ec2 associate-address --instance-id $INSTANCE_ID --allocation-id $ALLOC_ID --region $AWS_REGION

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $AWS_REGION \
    --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo "Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo ""
echo "Next steps:"
echo "1. SSH into instance: ssh -i $KEY_NAME.pem ec2-user@$PUBLIC_IP"
echo "2. Upload your code or clone from git"
echo "3. Create .env file with API keys"
echo "4. Run: docker-compose up -d"
echo ""
echo "Estimated monthly cost: ~\$8-15 (t3.micro/small)"
