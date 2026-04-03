# CloudWatch Logs Setup Guide

This guide explains how to set up AWS CloudWatch Logs to centralize, search, and monitor logs from your Lightsail instance running Docker containers.

## Overview

The CloudWatch agent collects:
- **Docker container logs** (nester-backend, nester-frontend, nester-caddy)
- **System logs** (/var/log/syslog)
- **Application metrics** (CPU, memory, disk usage)

## Prerequisites

1. AWS CLI configured on your Lightsail instance
2. IAM permissions for CloudWatch Logs (see IAM Setup below)
3. Access to the Lightsail instance via SSH

## Quick Setup

### Option 1: Automated Setup (Recommended)

Run the setup script on your Lightsail instance:

```bash
cd ~/nester-bot
chmod +x scripts/install-cloudwatch-agent.sh
sudo ./scripts/install-cloudwatch-agent.sh
```

### Option 2: Manual Setup

1. **Download and Install CloudWatch Agent:**
```bash
cd /tmp
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb
```

2. **Create Log Groups:**
```bash
aws logs create-log-group --log-group-name "/lightsail/nester-docker" --region ap-south-1
aws logs create-log-group --log-group-name "/lightsail/nester-system" --region ap-south-1

# Set retention to 30 days
aws logs put-retention-policy --log-group-name "/lightsail/nester-docker" --retention-in-days 30 --region ap-south-1
aws logs put-retention-policy --log-group-name "/lightsail/nester-system" --retention-in-days 30 --region ap-south-1
```

3. **Configure Agent:**
```bash
# Copy config file
sudo cp ~/nester-bot/scripts/cloudwatch-agent-config.json /opt/aws/amazon-cloudwatch-agent/bin/config.json

# Start agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -c file:/opt/aws/amazon-cloudwatch-agent/bin/config.json \
    -s
```

## IAM Permissions Setup

Since Lightsail instances don't support IAM roles directly, you need to configure IAM user credentials.

### Create IAM User for CloudWatch

1. Go to AWS IAM Console → Users → Create User
2. Name: `lightsail-cloudwatch-logs`
3. Attach policy: `CloudWatchAgentServerPolicy` (AWS managed policy)
4. Create access keys and configure on Lightsail:

```bash
aws configure
# Enter Access Key ID
# Enter Secret Access Key
# Region: ap-south-1
# Output format: json
```

### Required IAM Permissions

The user needs these permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:PutRetentionPolicy",
        "logs:DescribeLogStreams"
      ],
      "Resource": "arn:aws:logs:ap-south-1:*:log-group:/lightsail/*"
    }
  ]
}
```

## Configuration

The CloudWatch agent configuration is in `scripts/cloudwatch-agent-config.json`:

- **Docker Logs**: `/var/lib/docker/containers/*/*-json.log` → `/lightsail/nester-docker`
- **System Logs**: `/var/log/syslog` → `/lightsail/nester-system`
- **Metrics**: CPU, memory, disk usage → `NesterVoiceAI` namespace

## Monitoring Logs

### View Logs in AWS Console

1. Go to [CloudWatch Logs Console](https://console.aws.amazon.com/cloudwatch/home?region=ap-south-1#logsV2:log-groups)
2. Select log group: `/lightsail/nester-docker`
3. Click on a log stream to view logs

### View Logs via AWS CLI

```bash
# Tail logs in real-time
aws logs tail /lightsail/nester-docker --follow --region ap-south-1

# View last 100 log events
aws logs tail /lightsail/nester-docker --since 1h --region ap-south-1

# Filter for specific container
aws logs tail /lightsail/nester-docker --filter-pattern "nester-backend" --region ap-south-1
```

### CloudWatch Logs Insights Queries

Use CloudWatch Logs Insights for advanced querying:

**Find LightRAG-related logs:**
```sql
fields @timestamp, @message
| filter @message like /LightRAG|lightrag|RAG/
| sort @timestamp desc
| limit 50
```

**Find errors:**
```sql
fields @timestamp, @message
| filter @message like /error|Error|ERROR|exception|Exception/
| sort @timestamp desc
| limit 50
```

**Find specific container logs:**
```sql
fields @timestamp, @message
| filter @logStream like /nester-backend/
| sort @timestamp desc
| limit 100
```

**Monitor API errors:**
```sql
fields @timestamp, @message
| filter @message like /403|429|500|timeout/
| sort @timestamp desc
| limit 50
```

## Managing the Agent

### Check Agent Status
```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -m ec2 -a status
```

### Stop Agent
```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -m ec2 -a stop
```

### Start Agent
```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -m ec2 -a start
```

### Restart Agent
```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -m ec2 -a stop
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -m ec2 -a start
```

### Update Configuration
```bash
sudo cp ~/nester-bot/scripts/cloudwatch-agent-config.json /opt/aws/amazon-cloudwatch-agent/bin/config.json
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/bin/config.json -s
```

## Docker-Specific Tips

### View Container Logs Locally
```bash
# View backend logs
docker logs nester-backend --tail 100

# Follow logs in real-time
docker logs nester-backend -f

# Filter for LightRAG
docker logs nester-backend --tail 100 | grep -i lightrag

# View all container logs
docker-compose -f docker-compose.https.yml logs --tail 50
```

### Test Log Collection
```bash
# Generate a test log entry
docker exec nester-backend echo "Test log entry $(date)" >> /proc/1/fd/1

# Check if it appears in CloudWatch (may take a few seconds)
aws logs tail /lightsail/nester-docker --since 1m --region ap-south-1 | grep "Test log"
```

## Setting Up Alarms

Create CloudWatch alarms for important events:

### Error Rate Alarm
```bash
aws cloudwatch put-metric-alarm \
    --alarm-name nester-backend-errors \
    --alarm-description "Alert on high error rate" \
    --metric-name IncomingLogEvents \
    --namespace AWS/Logs \
    --statistic Sum \
    --period 300 \
    --threshold 10 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 1 \
    --region ap-south-1
```

## Troubleshooting

### Agent Not Sending Logs

1. **Check agent status:**
   ```bash
   sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -m ec2 -a status
   ```

2. **Check agent logs:**
   ```bash
   sudo cat /opt/aws/amazon-cloudwatch-agent/logs/amazon-cloudwatch-agent.log
   ```

3. **Verify IAM permissions:**
   ```bash
   aws logs describe-log-groups --region ap-south-1
   ```

4. **Check Docker log files exist:**
   ```bash
   ls -la /var/lib/docker/containers/*/*-json.log | head -5
   ```

### Logs Not Appearing in CloudWatch

- Wait 1-2 minutes for logs to appear (agent batches logs)
- Check log group exists: `aws logs describe-log-groups --region ap-south-1`
- Verify agent is running: `sudo systemctl status amazon-cloudwatch-agent`
- Check agent configuration: `sudo cat /opt/aws/amazon-cloudwatch-agent/bin/config.json`

## Cost Considerations

- **First 5 GB/month**: Free
- **After 5 GB**: $0.50 per GB ingested
- **Storage**: $0.03 per GB/month
- **Retention**: 30 days (configurable)

To reduce costs:
- Set appropriate log retention periods
- Filter unnecessary logs in agent config
- Use log level filtering (INFO, WARNING, ERROR only)

## Additional Resources

- [CloudWatch Agent Documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Install-CloudWatch-Agent.html)
- [CloudWatch Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html)
- [CloudWatch Pricing](https://aws.amazon.com/cloudwatch/pricing/)

