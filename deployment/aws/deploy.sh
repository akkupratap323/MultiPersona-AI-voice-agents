#!/bin/bash
# AWS ECS Deployment Script for Nester Conversational Bot
# This script builds, pushes, and deploys both frontend and backend services

set -e

# Configuration - UPDATE THESE VALUES
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="YOUR_ACCOUNT_ID"
BACKEND_REPO="nester-backend"
FRONTEND_REPO="nester-frontend"
ECS_CLUSTER="nester-cluster"
BACKEND_SERVICE="nester-backend-service"
FRONTEND_SERVICE="nester-frontend-service"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Nester Bot AWS Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}AWS CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Login to ECR
echo -e "${YELLOW}Logging in to AWS ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Create ECR repositories if they don't exist
echo -e "${YELLOW}Creating ECR repositories if they don't exist...${NC}"
aws ecr describe-repositories --repository-names $BACKEND_REPO --region $AWS_REGION 2>/dev/null || \
    aws ecr create-repository --repository-name $BACKEND_REPO --region $AWS_REGION

aws ecr describe-repositories --repository-names $FRONTEND_REPO --region $AWS_REGION 2>/dev/null || \
    aws ecr create-repository --repository-name $FRONTEND_REPO --region $AWS_REGION

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Build and push backend image
echo -e "${YELLOW}Building backend Docker image...${NC}"
docker build -t $BACKEND_REPO:latest .

echo -e "${YELLOW}Tagging and pushing backend image...${NC}"
docker tag $BACKEND_REPO:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$BACKEND_REPO:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$BACKEND_REPO:latest

# Build and push frontend image
echo -e "${YELLOW}Building frontend Docker image...${NC}"
cd client
docker build -t $FRONTEND_REPO:latest .

echo -e "${YELLOW}Tagging and pushing frontend image...${NC}"
docker tag $FRONTEND_REPO:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$FRONTEND_REPO:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$FRONTEND_REPO:latest

cd "$PROJECT_ROOT"

# Update ECS services (force new deployment)
echo -e "${YELLOW}Updating ECS services...${NC}"
aws ecs update-service --cluster $ECS_CLUSTER --service $BACKEND_SERVICE --force-new-deployment --region $AWS_REGION
aws ecs update-service --cluster $ECS_CLUSTER --service $FRONTEND_SERVICE --force-new-deployment --region $AWS_REGION

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}Note: It may take a few minutes for the new containers to be fully deployed.${NC}"
echo -e "${YELLOW}Check the ECS console for deployment status.${NC}"
