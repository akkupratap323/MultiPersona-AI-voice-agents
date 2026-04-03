# AWS Deployment Guide for Nester Conversational Bot

This guide covers deploying both the frontend and backend of the Nester Conversational Bot to AWS using ECS Fargate.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS Cloud                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    VPC (10.0.0.0/16)                      │   │
│  │  ┌───────────────┐         ┌───────────────┐             │   │
│  │  │ Public Subnet │         │ Public Subnet │             │   │
│  │  │  (10.0.1.0/24)│         │  (10.0.2.0/24)│             │   │
│  │  └───────┬───────┘         └───────┬───────┘             │   │
│  │          │                         │                      │   │
│  │  ┌───────┴─────────────────────────┴───────┐             │   │
│  │  │         Application Load Balancer        │             │   │
│  │  │    (Frontend ALB + Backend ALB)          │             │   │
│  │  └───────┬─────────────────────────┬───────┘             │   │
│  │          │                         │                      │   │
│  │  ┌───────▼───────┐         ┌───────▼───────┐             │   │
│  │  │   Frontend    │         │    Backend    │             │   │
│  │  │   (Nginx)     │ ──────► │  (FastAPI)    │             │   │
│  │  │   Port 80     │         │  Port 7860    │             │   │
│  │  └───────────────┘         └───────────────┘             │   │
│  │                                    │                      │   │
│  │                            ┌───────▼───────┐             │   │
│  │                            │  External APIs │             │   │
│  │                            │ - Deepgram     │             │   │
│  │                            │ - OpenAI       │             │   │
│  │                            │ - Pinecone     │             │   │
│  │                            └───────────────┘             │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **Docker** installed and running
4. **API Keys** for:
   - Deepgram (STT)
   - OpenAI (LLM)
   - Pinecone (Vector DB) - if using RAG

## Quick Start

### Option 1: Using CloudFormation (Recommended)

1. **Create ECR Repositories and Push Images:**
   ```bash
   # Set your AWS region and account ID
   export AWS_REGION=us-east-1
   export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

   # Login to ECR
   aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

   # Create repositories
   aws ecr create-repository --repository-name nester-backend --region $AWS_REGION
   aws ecr create-repository --repository-name nester-frontend --region $AWS_REGION

   # Build and push backend
   docker build -t nester-backend .
   docker tag nester-backend:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/nester-backend:latest
   docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/nester-backend:latest

   # Build and push frontend
   cd client
   docker build -t nester-frontend .
   docker tag nester-frontend:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/nester-frontend:latest
   docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/nester-frontend:latest
   cd ..
   ```

2. **Store API Keys in AWS Secrets Manager:**
   ```bash
   aws secretsmanager create-secret \
     --name nester/api-keys \
     --secret-string '{
       "DEEPGRAM_API_KEY": "your-deepgram-key",
       "OPENAI_API_KEY": "your-openai-key",
       "PINECONE_API_KEY": "your-pinecone-key",
       "PINECONE_INDEX": "voice-assistant-rag"
     }' \
     --region $AWS_REGION
   ```

3. **Deploy CloudFormation Stack:**
   ```bash
   aws cloudformation create-stack \
     --stack-name nester-bot \
     --template-body file://aws/cloudformation-template.yaml \
     --parameters \
       ParameterKey=BackendImage,ParameterValue=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/nester-backend:latest \
       ParameterKey=FrontendImage,ParameterValue=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/nester-frontend:latest \
     --capabilities CAPABILITY_NAMED_IAM \
     --region $AWS_REGION
   ```

4. **Get the Frontend URL:**
   ```bash
   aws cloudformation describe-stacks \
     --stack-name nester-bot \
     --query 'Stacks[0].Outputs[?OutputKey==`FrontendURL`].OutputValue' \
     --output text \
     --region $AWS_REGION
   ```

### Option 2: Using Deploy Script

1. **Edit Configuration:**
   Edit `aws/deploy.sh` and update these values:
   ```bash
   AWS_REGION="us-east-1"
   AWS_ACCOUNT_ID="YOUR_ACCOUNT_ID"
   ```

2. **Run Deployment:**
   ```bash
   chmod +x aws/deploy.sh
   ./aws/deploy.sh
   ```

## Local Testing with Docker Compose

Before deploying to AWS, test locally:

```bash
# Create a .env file with your API keys
cp env.example .env
# Edit .env with your actual API keys

# Start services
docker-compose up --build

# Access frontend at http://localhost:80
# Backend API at http://localhost:7860
```

## Configuration

### Environment Variables

**Backend (required):**
| Variable | Description |
|----------|-------------|
| `DEEPGRAM_API_KEY` | Deepgram API key for STT |
| `OPENAI_API_KEY` | OpenAI API key for LLM |
| `PINECONE_API_KEY` | Pinecone API key (if using RAG) |
| `PINECONE_INDEX` | Pinecone index name |

**Backend (optional):**
| Variable | Default | Description |
|----------|---------|-------------|
| `FASTAPI_HOST` | 0.0.0.0 | FastAPI bind host |
| `FASTAPI_PORT` | 7860 | FastAPI port |
| `WEBSOCKET_PORT` | 8765 | WebSocket server port |
| `LOG_LEVEL` | INFO | Logging level |

**Frontend:**
| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_URL` | http://backend:7860 | Backend API URL |

## WebSocket Considerations

The Nester Bot uses WebSocket connections for real-time audio streaming. Important considerations:

1. **ALB Configuration**: The CloudFormation template configures ALB with WebSocket support (long timeout, sticky sessions).

2. **SSL/TLS**: For production, add HTTPS listeners to the ALB and use WSS for WebSocket connections.

3. **Connection Timeout**: WebSocket connections have a 86400-second (24 hour) timeout configured.

## Scaling

### Horizontal Scaling

Update the desired count in ECS service:
```bash
aws ecs update-service \
  --cluster nester-cluster \
  --service nester-backend-service \
  --desired-count 2 \
  --region $AWS_REGION
```

### Auto Scaling

Add this to your CloudFormation for auto-scaling:
```yaml
BackendScalingTarget:
  Type: AWS::ApplicationAutoScaling::ScalableTarget
  Properties:
    MaxCapacity: 4
    MinCapacity: 1
    ResourceId: !Sub service/${ECSCluster}/nester-backend-service
    ScalableDimension: ecs:service:DesiredCount
    ServiceNamespace: ecs

BackendScalingPolicy:
  Type: AWS::ApplicationAutoScaling::ScalingPolicy
  Properties:
    PolicyName: BackendCPUScaling
    PolicyType: TargetTrackingScaling
    ScalingTargetId: !Ref BackendScalingTarget
    TargetTrackingScalingPolicyConfiguration:
      TargetValue: 70
      PredefinedMetricSpecification:
        PredefinedMetricType: ECSServiceAverageCPUUtilization
```

## Monitoring

### CloudWatch Logs

View logs:
```bash
# Backend logs
aws logs tail /ecs/nester-backend --follow --region $AWS_REGION

# Frontend logs
aws logs tail /ecs/nester-frontend --follow --region $AWS_REGION
```

### Health Checks

- Frontend: `GET /` (nginx)
- Backend: `GET /status` (FastAPI)

## Cost Optimization

1. **Fargate Spot**: The template uses Fargate Spot for cost savings (up to 70% discount).

2. **Right-sizing**:
   - Backend: 512 CPU, 1024 MB memory
   - Frontend: 256 CPU, 512 MB memory

   Adjust based on your load patterns.

3. **NAT Gateway**: The current setup uses public subnets with public IPs to avoid NAT Gateway costs.

## Troubleshooting

### Container Won't Start

1. Check CloudWatch logs:
   ```bash
   aws logs tail /ecs/nester-backend --since 1h --region $AWS_REGION
   ```

2. Verify secrets are accessible:
   ```bash
   aws secretsmanager get-secret-value --secret-id nester/api-keys --region $AWS_REGION
   ```

### WebSocket Connection Fails

1. Check security group allows WebSocket ports (8765)
2. Verify ALB target group health
3. Check backend logs for connection errors

### High Latency

1. Use a region closer to your users
2. Check if external API (Deepgram, OpenAI) is responding slowly
3. Consider caching frequently accessed data

## Cleanup

Delete all resources:
```bash
# Delete CloudFormation stack
aws cloudformation delete-stack --stack-name nester-bot --region $AWS_REGION

# Delete ECR images
aws ecr batch-delete-image --repository-name nester-backend --image-ids imageTag=latest --region $AWS_REGION
aws ecr batch-delete-image --repository-name nester-frontend --image-ids imageTag=latest --region $AWS_REGION

# Delete ECR repositories
aws ecr delete-repository --repository-name nester-backend --region $AWS_REGION
aws ecr delete-repository --repository-name nester-frontend --region $AWS_REGION

# Delete secrets
aws secretsmanager delete-secret --secret-id nester/api-keys --force-delete-without-recovery --region $AWS_REGION
```

## Security Best Practices

1. **Use HTTPS**: Add ACM certificate and HTTPS listener to ALB
2. **Restrict Security Groups**: Limit inbound traffic to only necessary ports
3. **Rotate API Keys**: Regularly rotate secrets in Secrets Manager
4. **Enable VPC Flow Logs**: For network traffic monitoring
5. **Use WAF**: Add AWS WAF for web application protection
