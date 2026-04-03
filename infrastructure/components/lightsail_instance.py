"""
Lightsail instance construct for NesterAI.

Uses L1 constructs for Lightsail resources.
"""

from constructs import Construct
from aws_cdk import (
    CfnOutput,
    aws_lightsail as lightsail,
)

from utils.config_loader import NesterConfig


class LightsailInstance(Construct):
    """
    Creates a Lightsail instance configured for NesterAI Voice Assistant.

    Includes:
    - Instance with specified bundle and blueprint
    - Firewall rules for required ports
    - User data script for Docker and application setup
    - ECR authentication for pulling container images
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        config: NesterConfig,
        secret_arn: str,
        backend_image_uri: str,
        frontend_image_uri: str,
    ) -> None:
        super().__init__(scope, id)

        self.config = config
        self.backend_image_uri = backend_image_uri
        self.frontend_image_uri = frontend_image_uri
        prefix = config.resource_prefix

        # Build firewall rules from config
        networking_ports = []
        for port_config in config.lightsail.networking.ports:
            cidrs = port_config.cidrs if port_config.cidrs else ["0.0.0.0/0"]
            for cidr in cidrs:
                networking_ports.append(
                    lightsail.CfnInstance.PortProperty(
                        from_port=port_config.port,
                        to_port=port_config.port,
                        protocol=port_config.protocol.upper(),
                        cidrs=[cidr],
                    )
                )

        # Generate user data script
        user_data = self._generate_user_data(secret_arn)

        # Create the Lightsail instance (L1 construct)
        self.instance = lightsail.CfnInstance(
            self,
            "Instance",
            instance_name=f"{prefix}-instance",
            availability_zone=config.availability_zone,
            blueprint_id=config.lightsail.instance.blueprint_id,
            bundle_id=config.lightsail.instance.bundle_id,
            networking=lightsail.CfnInstance.NetworkingProperty(
                ports=networking_ports,
            ),
            user_data=user_data,
            tags=[
                {"key": "Name", "value": f"{prefix}-instance"},
                {"key": "Environment", "value": config.environment},
                {"key": "Project", "value": config.project.name},
                {"key": "ManagedBy", "value": "CDK"},
            ],
        )

        # Store instance name for static IP attachment
        self.instance_name = self.instance.instance_name

        # Outputs
        CfnOutput(
            self,
            "InstanceName",
            value=self.instance.instance_name,
            description="Lightsail instance name",
        )

    def _generate_user_data(self, secret_arn: str) -> str:
        """
        Generate the user data script for instance initialization.

        This script:
        1. Installs Docker and Docker Compose
        2. Configures swap space
        3. Authenticates with ECR
        4. Pulls and runs the application containers
        """
        config = self.config
        app = config.application
        region = config.aws.region

        # Extract ECR registry URL from image URI
        ecr_registry = self.backend_image_uri.split("/")[0]

        # Build environment variables for the script
        env_vars = {
            "FASTAPI_HOST": app.server.fastapi_host,
            "FASTAPI_PORT": str(app.server.fastapi_port),
            "WEBSOCKET_HOST": app.server.websocket_host,
            "WEBSOCKET_PORT": str(app.server.websocket_port),
            "SESSION_TIMEOUT": str(app.server.session_timeout),
            "LOG_LEVEL": app.server.log_level,
        }

        if app.domain.name:
            env_vars["DOMAIN"] = app.domain.name
            env_vars["PUBLIC_URL"] = (
                f"https://{app.domain.name}"
                if app.domain.use_https
                else f"http://{app.domain.name}"
            )

        # User data script (runs on first boot)
        user_data = f"""#!/bin/bash
set -e

# Log all output
exec > >(tee /var/log/user-data.log) 2>&1
echo "Starting NesterAI instance setup..."

# Update system
yum update -y

# Install Docker
yum install -y docker
systemctl enable docker
systemctl start docker

# Install Docker Compose v2
mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Add ec2-user to docker group
usermod -aG docker ec2-user

# Create swap space (for 4GB instance)
if [ ! -f /swapfile ]; then
    dd if=/dev/zero of=/swapfile bs=1M count=2048
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile swap swap defaults 0 0' >> /etc/fstab
fi

# Install AWS CLI v2
if ! command -v aws &> /dev/null; then
    curl "https://awscli.amazonaws.com/awscli-exe-linux-$(uname -m).zip" -o "awscliv2.zip"
    unzip -q awscliv2.zip
    ./aws/install
    rm -rf aws awscliv2.zip
fi

# Create application directory
mkdir -p /opt/nester
cd /opt/nester

# Configuration
REGION="{region}"
SECRET_ARN="{secret_arn}"
ECR_REGISTRY="{ecr_registry}"
BACKEND_IMAGE="{self.backend_image_uri}"
FRONTEND_IMAGE="{self.frontend_image_uri}"

# Fetch secrets from AWS Secrets Manager
echo "Fetching secrets from Secrets Manager..."
SECRET_JSON=$(aws secretsmanager get-secret-value --secret-id "$SECRET_ARN" --region "$REGION" --query SecretString --output text 2>/dev/null || echo "{{}}")

# Create .env file
echo "Creating .env file..."
cat > /opt/nester/.env << 'ENVEOF'
# Auto-generated environment file
# Server Configuration
{chr(10).join(f'{k}={v}' for k, v in env_vars.items())}
ENVEOF

# Append secrets to .env file (skip placeholders)
echo "$SECRET_JSON" | python3 -c "
import sys, json
try:
    secrets = json.load(sys.stdin)
    for key, value in secrets.items():
        if not str(value).startswith('PLACEHOLDER_'):
            print(f'{{key}}={{value}}')
except:
    pass
" >> /opt/nester/.env

# Create ECR login script (runs before docker compose)
cat > /opt/nester/ecr-login.sh << 'ECREOF'
#!/bin/bash
aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {ecr_registry}
ECREOF
chmod +x /opt/nester/ecr-login.sh

# Create docker-compose.yml
cat > /opt/nester/docker-compose.yml << 'COMPOSEEOF'
services:
  backend:
    image: {self.backend_image_uri}
    container_name: nester-backend
    restart: always
    ports:
      - "{app.server.fastapi_port}:{app.server.fastapi_port}"
      - "{app.server.websocket_port}:{app.server.websocket_port}"
    env_file:
      - .env
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{app.server.fastapi_port}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  frontend:
    image: {self.frontend_image_uri}
    container_name: nester-frontend
    restart: always
    ports:
      - "80:80"
    environment:
      - VITE_BACKEND_URL=http://localhost:{app.server.fastapi_port}
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:80/"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  default:
    name: nester-network
COMPOSEEOF

# Login to ECR
echo "Authenticating with ECR..."
/opt/nester/ecr-login.sh || echo "Warning: ECR login failed. Images may not exist yet."

# Pull and start containers
echo "Pulling container images..."
docker compose pull || echo "Warning: Could not pull images. They may not exist yet. Push images and restart."

echo "Starting containers..."
docker compose up -d || echo "Warning: Could not start containers. Check images and logs."

# Create systemd service for auto-start (includes ECR login)
cat > /etc/systemd/system/nester.service << 'SERVICEEOF'
[Unit]
Description=NesterAI Voice Assistant
After=docker.service network-online.target
Requires=docker.service
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/nester
ExecStartPre=/opt/nester/ecr-login.sh
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
ExecReload=/usr/bin/docker compose pull && /usr/bin/docker compose up -d

[Install]
WantedBy=multi-user.target
SERVICEEOF

systemctl daemon-reload
systemctl enable nester.service

# Create helper scripts
cat > /opt/nester/deploy.sh << 'DEPLOYEOF'
#!/bin/bash
# Deploy script - pulls latest images and restarts
set -e
cd /opt/nester
./ecr-login.sh
docker compose pull
docker compose up -d --force-recreate
echo "Deployment complete!"
DEPLOYEOF
chmod +x /opt/nester/deploy.sh

cat > /opt/nester/logs.sh << 'LOGSEOF'
#!/bin/bash
# View logs
cd /opt/nester
docker compose logs -f
LOGSEOF
chmod +x /opt/nester/logs.sh

echo "========================================="
echo "NesterAI instance setup complete!"
echo "========================================="
echo "Application directory: /opt/nester"
echo "Deploy new images:     /opt/nester/deploy.sh"
echo "View logs:             /opt/nester/logs.sh"
echo "Restart service:       sudo systemctl restart nester"
echo ""
echo "Note: If images don't exist yet, push to ECR first then run:"
echo "      /opt/nester/deploy.sh"
"""
        return user_data