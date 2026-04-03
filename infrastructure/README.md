# NesterAI Infrastructure (AWS CDK)

AWS CDK (Python) infrastructure for NesterAI Voice Assistant deployed on AWS Lightsail.

**Default Region:** `us-west-2` (Oregon)

## Directory Structure

```
infrastructure/
├── app.py                      # CDK app entry point
├── cdk.json                    # CDK configuration
├── requirements.txt            # Python dependencies
├── config/
│   ├── base.yaml               # Base/shared configuration
│   └── dev.yaml                # Dev environment overrides
├── components/
│   ├── ecr.py                  # ECR repositories (L2 construct)
│   ├── secrets.py              # Secrets Manager (L2 construct)
│   ├── lightsail_instance.py   # Lightsail instance (L1 construct)
│   └── lightsail_networking.py # Static IP (L1 construct)
├── stacks/
│   └── lightsail_stack.py      # Lightsail infrastructure stack
├── ci-cd/
│   └── github-actions-example.yml  # Sample CI/CD workflow
└── utils/
    └── config_loader.py        # YAML configuration loader
```

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Python 3.11+**
3. **AWS CDK CLI** (`npm install -g aws-cdk`)

## Setup

```bash
cd infrastructure

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Bootstrap CDK (first time only, per account/region)
cdk bootstrap aws://ACCOUNT_ID/REGION
```

## Configuration

All configuration is managed via YAML files in the `config/` directory:

- **base.yaml**: Shared configuration (don't put secrets here)
- **staging.yaml**: Staging environment overrides
- **production.yaml**: Production environment overrides

### Key Configuration Options

```yaml
# config/production.yaml
lightsail:
  instance:
    bundle_id: "medium_3_0"  # 4GB RAM, 2 vCPUs
    blueprint_id: "amazon_linux_2023"

application:
  domain:
    name: "voice.yourdomain.com"
    use_https: true
```

## Deployment

### Deploy Staging

```bash
cdk deploy --context environment=staging
```

### Deploy Production

```bash
cdk deploy --context environment=production
```

### Other Commands

```bash
# Preview changes without deploying
cdk diff --context environment=staging

# Generate CloudFormation template
cdk synth --context environment=staging

# Destroy stack (careful!)
cdk destroy --context environment=staging
```

## Post-Deployment Steps

### 1. Push Container Images to ECR

CDK creates empty ECR repositories. Push images before the instance can run:

```bash
# Get ECR login (use the EcrLoginCommand from CDK output)
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com

# Build and push backend
cd /path/to/NesterAIBot
docker build -t nester-ai-staging-backend -f deployment/docker/Dockerfile .
docker tag nester-ai-staging-backend:latest ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/nester-ai-staging-backend:latest
docker push ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/nester-ai-staging-backend:latest

# Build and push frontend
cd client
docker build -t nester-ai-staging-frontend .
docker tag nester-ai-staging-frontend:latest ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/nester-ai-staging-frontend:latest
docker push ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/nester-ai-staging-frontend:latest
```

### 2. Configure Secrets

Update the Secrets Manager secret with your actual API keys:

```bash
# Create secrets.json
cat > secrets.json << 'EOF'
{
  "DEEPGRAM_API_KEY": "your-actual-key",
  "GOOGLE_API_KEY": "your-actual-key",
  "RESEMBLE_API_KEY": "your-actual-key",
  "LIGHTRAG_API_KEY": "your-actual-key",
  "LIGHTRAG_BASE_URL": "https://your-lightrag-url"
}
EOF

# Update the secret
aws secretsmanager put-secret-value \
  --secret-id nester/staging/api-keys \
  --secret-string file://secrets.json \
  --region us-west-2

# Clean up
rm secrets.json
```

### 3. Deploy to Instance

SSH into the instance and run the deploy script:

```bash
ssh -i ~/.ssh/LightsailDefaultKey-us-west-2.pem ec2-user@STATIC_IP

# On the instance:
sudo /opt/nester/deploy.sh
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        AWS Cloud                             │
│                                                              │
│  ┌─────────────────┐     ┌─────────────────────────────┐   │
│  │   ECR Repos     │     │      Lightsail Instance      │   │
│  │  ┌───────────┐  │     │  ┌─────────┐  ┌─────────┐   │   │
│  │  │ backend   │──┼────▶│  │ Backend │  │Frontend │   │   │
│  │  └───────────┘  │     │  │ :7860   │  │  :80    │   │   │
│  │  ┌───────────┐  │     │  └─────────┘  └─────────┘   │   │
│  │  │ frontend  │──┼────▶│                             │   │
│  │  └───────────┘  │     └─────────────────────────────┘   │
│  └─────────────────┘                  │                     │
│                                  Static IP                  │
│  ┌─────────────────┐                  │                     │
│  │ Secrets Manager │◀─────────────────┘                     │
│  │   (API Keys)    │                                        │
│  └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
```

## CI/CD Integration

After CDK deploys, use these outputs in your GitHub Actions:

```yaml
# .github/workflows/deploy.yml
env:
  AWS_REGION: us-west-2
  ECR_BACKEND: ${{ secrets.ECR_BACKEND_URI }}   # From CDK output
  ECR_FRONTEND: ${{ secrets.ECR_FRONTEND_URI }} # From CDK output

jobs:
  build-and-push:
    steps:
      - name: Login to ECR
        run: |
          aws ecr get-login-password --region $AWS_REGION | \
            docker login --username AWS --password-stdin $ECR_BACKEND

      - name: Build and push
        run: |
          docker build -t $ECR_BACKEND:${{ github.sha }} .
          docker push $ECR_BACKEND:${{ github.sha }}
          docker tag $ECR_BACKEND:${{ github.sha }} $ECR_BACKEND:latest
          docker push $ECR_BACKEND:latest
```

## Lightsail Bundle IDs

| Bundle ID | RAM | vCPUs | Storage | Price/mo |
|-----------|-----|-------|---------|----------|
| nano_3_0 | 512MB | 2 | 20GB | $3.50 |
| micro_3_0 | 1GB | 2 | 40GB | $5 |
| small_3_0 | 2GB | 1 | 60GB | $10 |
| medium_3_0 | 4GB | 2 | 80GB | $20 |
| large_3_0 | 8GB | 2 | 160GB | $40 |
| xlarge_3_0 | 16GB | 4 | 320GB | $80 |

## Troubleshooting

### View instance logs

```bash
ssh -i ~/.ssh/LightsailDefaultKey-us-west-2.pem ec2-user@STATIC_IP
sudo cat /var/log/user-data.log
```

### Check container status

```bash
cd /opt/nester
sudo docker compose ps
sudo docker compose logs -f
```

### Rebuild containers

```bash
cd /opt/nester
sudo docker compose pull
sudo docker compose up -d --force-recreate
```

## Notes

- **L1 Constructs**: Lightsail uses L1 (CloudFormation-level) constructs as L2 constructs are not available
- **Secrets**: Created with placeholder values - update via AWS Console or CLI after deployment
- **Static IP**: Automatically attached to instance for consistent endpoint
- **User Data**: Instance bootstraps Docker, pulls images, and starts containers on first boot