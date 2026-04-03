"""
Lightsail instance using CDK Custom Resource.

Uses AwsCustomResource to call Lightsail SDK APIs directly,
bypassing CloudFormation resource type limitations.
"""

from constructs import Construct
from aws_cdk import (
    CfnOutput,
    CustomResource,
    Duration,
    custom_resources as cr,
    aws_iam as iam,
    aws_logs as logs,
)

from utils.config_loader import NesterConfig


class LightsailCustomResource(Construct):
    """
    Creates Lightsail instance and static IP using AWS SDK calls.

    This works around the CloudFormation limitation where
    AWS::Lightsail::Instance is not supported in all regions.
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        config: NesterConfig,
        api_keys_secret_arn: str,
        ecr_credentials_secret_arn: str,
        backend_image_uri: str,
        frontend_image_uri: str,
    ) -> None:
        super().__init__(scope, id)

        self.config = config
        self.api_keys_secret_arn = api_keys_secret_arn
        self.ecr_credentials_secret_arn = ecr_credentials_secret_arn
        self.backend_image_uri = backend_image_uri
        self.frontend_image_uri = frontend_image_uri
        prefix = config.resource_prefix
        region = config.aws.region

        self.instance_name = f"{prefix}-instance"
        self.static_ip_name = f"{prefix}-static-ip"

        # Build port info for firewall
        port_infos = []
        for port_config in config.lightsail.networking.ports:
            cidrs = port_config.cidrs if port_config.cidrs else ["0.0.0.0/0"]
            port_infos.append({
                "fromPort": port_config.port,
                "toPort": port_config.port,
                "protocol": port_config.protocol.lower(),
                "cidrs": cidrs,
            })

        # Generate user data script
        user_data = self._generate_user_data()

        # Tags for the instance
        tags = [
            {"key": "Name", "value": self.instance_name},
            {"key": "Environment", "value": config.environment},
            {"key": "Project", "value": config.project.name},
            {"key": "ManagedBy", "value": "CDK"},
        ]

        # Create a shared IAM role with all Lightsail permissions
        # This avoids race conditions with multiple AwsCustomResource sharing a Lambda
        lightsail_role = iam.Role(
            self,
            "LightsailCustomResourceRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
            ],
        )

        # Add all Lightsail permissions to the role
        lightsail_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    # Instance management
                    "lightsail:CreateInstances",
                    "lightsail:DeleteInstance",
                    "lightsail:GetInstance",
                    "lightsail:TagResource",
                    # Port/firewall management
                    "lightsail:PutInstancePublicPorts",
                    "lightsail:GetInstancePortStates",
                    # Static IP management
                    "lightsail:AllocateStaticIp",
                    "lightsail:ReleaseStaticIp",
                    "lightsail:GetStaticIp",
                    "lightsail:AttachStaticIp",
                    "lightsail:DetachStaticIp",
                ],
                resources=["*"],
            )
        )

        # Create Lightsail Instance via SDK
        self.instance_resource = cr.AwsCustomResource(
            self,
            "LightsailInstance",
            install_latest_aws_sdk=False,
            log_retention=logs.RetentionDays.ONE_WEEK,
            role=lightsail_role,
            on_create=cr.AwsSdkCall(
                service="Lightsail",
                action="createInstances",
                region=region,
                parameters={
                    "instanceNames": [self.instance_name],
                    "availabilityZone": config.availability_zone,
                    "blueprintId": config.lightsail.instance.blueprint_id,
                    "bundleId": config.lightsail.instance.bundle_id,
                    "userData": user_data,
                    "tags": tags,
                },
                physical_resource_id=cr.PhysicalResourceId.of(self.instance_name),
            ),
            on_update=cr.AwsSdkCall(
                service="Lightsail",
                action="getInstance",
                region=region,
                parameters={
                    "instanceName": self.instance_name,
                },
                physical_resource_id=cr.PhysicalResourceId.of(self.instance_name),
            ),
            on_delete=cr.AwsSdkCall(
                service="Lightsail",
                action="deleteInstance",
                region=region,
                parameters={
                    "instanceName": self.instance_name,
                },
            ),
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(resources=["*"]),
        )

        # Configure firewall ports after instance is created
        self.ports_resource = cr.AwsCustomResource(
            self,
            "LightsailPorts",
            install_latest_aws_sdk=False,
            log_retention=logs.RetentionDays.ONE_WEEK,
            role=lightsail_role,
            on_create=cr.AwsSdkCall(
                service="Lightsail",
                action="putInstancePublicPorts",
                region=region,
                parameters={
                    "instanceName": self.instance_name,
                    "portInfos": port_infos,
                },
                physical_resource_id=cr.PhysicalResourceId.of(f"{self.instance_name}-ports"),
            ),
            on_update=cr.AwsSdkCall(
                service="Lightsail",
                action="putInstancePublicPorts",
                region=region,
                parameters={
                    "instanceName": self.instance_name,
                    "portInfos": port_infos,
                },
                physical_resource_id=cr.PhysicalResourceId.of(f"{self.instance_name}-ports"),
            ),
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(resources=["*"]),
        )
        self.ports_resource.node.add_dependency(self.instance_resource)

        # Allocate and attach Static IP if enabled
        self.static_ip_resource = None
        if config.lightsail.static_ip.enabled:
            # Allocate static IP
            self.static_ip_resource = cr.AwsCustomResource(
                self,
                "LightsailStaticIp",
                install_latest_aws_sdk=False,
                log_retention=logs.RetentionDays.ONE_WEEK,
                role=lightsail_role,
                on_create=cr.AwsSdkCall(
                    service="Lightsail",
                    action="allocateStaticIp",
                    region=region,
                    parameters={
                        "staticIpName": self.static_ip_name,
                    },
                    physical_resource_id=cr.PhysicalResourceId.of(self.static_ip_name),
                ),
                on_delete=cr.AwsSdkCall(
                    service="Lightsail",
                    action="releaseStaticIp",
                    region=region,
                    parameters={
                        "staticIpName": self.static_ip_name,
                    },
                ),
                policy=cr.AwsCustomResourcePolicy.from_sdk_calls(resources=["*"]),
            )

            # Attach static IP to instance
            self.attach_ip_resource = cr.AwsCustomResource(
                self,
                "LightsailAttachIp",
                install_latest_aws_sdk=False,
                log_retention=logs.RetentionDays.ONE_WEEK,
                role=lightsail_role,
                on_create=cr.AwsSdkCall(
                    service="Lightsail",
                    action="attachStaticIp",
                    region=region,
                    parameters={
                        "staticIpName": self.static_ip_name,
                        "instanceName": self.instance_name,
                    },
                    physical_resource_id=cr.PhysicalResourceId.of(f"{self.static_ip_name}-attach"),
                ),
                on_update=cr.AwsSdkCall(
                    service="Lightsail",
                    action="attachStaticIp",
                    region=region,
                    parameters={
                        "staticIpName": self.static_ip_name,
                        "instanceName": self.instance_name,
                    },
                    physical_resource_id=cr.PhysicalResourceId.of(f"{self.static_ip_name}-attach"),
                ),
                on_delete=cr.AwsSdkCall(
                    service="Lightsail",
                    action="detachStaticIp",
                    region=region,
                    parameters={
                        "staticIpName": self.static_ip_name,
                    },
                ),
                policy=cr.AwsCustomResourcePolicy.from_sdk_calls(resources=["*"]),
            )
            # Dependencies: instance must exist, static IP must be allocated
            self.attach_ip_resource.node.add_dependency(self.instance_resource)
            self.attach_ip_resource.node.add_dependency(self.static_ip_resource)

            # Get static IP address for outputs
            self.get_ip_resource = cr.AwsCustomResource(
                self,
                "GetStaticIp",
                install_latest_aws_sdk=False,
                log_retention=logs.RetentionDays.ONE_WEEK,
                role=lightsail_role,
                on_create=cr.AwsSdkCall(
                    service="Lightsail",
                    action="getStaticIp",
                    region=region,
                    parameters={
                        "staticIpName": self.static_ip_name,
                    },
                    physical_resource_id=cr.PhysicalResourceId.of(f"{self.static_ip_name}-get"),
                ),
                on_update=cr.AwsSdkCall(
                    service="Lightsail",
                    action="getStaticIp",
                    region=region,
                    parameters={
                        "staticIpName": self.static_ip_name,
                    },
                    physical_resource_id=cr.PhysicalResourceId.of(f"{self.static_ip_name}-get"),
                ),
                policy=cr.AwsCustomResourcePolicy.from_sdk_calls(resources=["*"]),
            )
            self.get_ip_resource.node.add_dependency(self.attach_ip_resource)

            # Store IP address reference
            self.ip_address = self.get_ip_resource.get_response_field("staticIp.ipAddress")

        # Outputs
        CfnOutput(
            self,
            "InstanceName",
            value=self.instance_name,
            description="Lightsail instance name",
        )

    def _generate_user_data(self) -> str:
        """
        Generate the user data script for instance initialization.
        Includes Caddy reverse proxy for HTTPS when domain is configured.
        Fetches AWS credentials from Secrets Manager for ECR access.
        """
        config = self.config
        app = config.application
        region = config.aws.region
        use_https = app.domain.use_https and app.domain.name

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

        # Generate docker-compose based on HTTPS mode
        if use_https:
            docker_compose = self._generate_https_compose(app)
            caddyfile_section = self._generate_caddyfile(app)
        else:
            docker_compose = self._generate_http_compose(app)
            caddyfile_section = ""

        user_data = f"""#!/bin/bash
set -e

# Log all output
exec > >(tee /var/log/user-data.log) 2>&1
echo "Starting NesterAI instance setup..."

# Update system
yum update -y

# Install Docker
yum install -y docker jq
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
API_KEYS_SECRET_ARN="{self.api_keys_secret_arn}"
ECR_CREDENTIALS_SECRET_ARN="{self.ecr_credentials_secret_arn}"
ECR_REGISTRY="{ecr_registry}"
BACKEND_IMAGE="{self.backend_image_uri}"
FRONTEND_IMAGE="{self.frontend_image_uri}"

# ============================================
# IMPORTANT: Lightsail Cross-Account Limitation
# ============================================
# Lightsail instances use AWS-managed role (AmazonLightsailInstanceRole) in AWS's
# service account (790779513465), NOT your account. This means:
# - Cannot access your Secrets Manager
# - Cannot access your ECR directly
#
# MANUAL SETUP REQUIRED (one-time after instance creation):
# 1. SSH to instance: ssh -i ~/.ssh/LightsailDefaultKey-{region}.pem ec2-user@<IP>
# 2. Get ECR credentials from Secrets Manager (from local machine):
#    aws secretsmanager get-secret-value --secret-id {self.ecr_credentials_secret_arn} \
#        --region {region} --query SecretString --output text
# 3. Configure AWS CLI on instance: aws configure
# 4. Run: /opt/nester/setup-secrets.sh
# 5. Run: /opt/nester/deploy.sh
# ============================================

# Create placeholder .env with server config (secrets added manually)
echo "Creating base .env file..."

# Create .env file with server configuration
cat > /opt/nester/.env << 'ENVEOF'
# Auto-generated environment file
# Server Configuration
{chr(10).join(f'{k}={v}' for k, v in env_vars.items())}

# API Keys - populate by running: /opt/nester/setup-secrets.sh
# Or manually add your keys below
ENVEOF

# Set proper ownership
chown ec2-user:ec2-user /opt/nester/.env
chmod 644 /opt/nester/.env

# ============================================
# STEP 1: Create ECR login script
# ============================================
cat > /opt/nester/ecr-login.sh << 'ECREOF'
#!/bin/bash
# Login to ECR (requires AWS credentials to be configured)
if ! aws sts get-caller-identity &>/dev/null; then
    echo "ERROR: AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi
aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {ecr_registry}
ECREOF
chmod +x /opt/nester/ecr-login.sh

{caddyfile_section}

# ============================================
# STEP 4: Create docker-compose.yml
# ============================================
cat > /opt/nester/docker-compose.yml << 'COMPOSEEOF'
{docker_compose}
COMPOSEEOF

# ============================================
# STEP 5: Create setup-secrets script
# ============================================
cat > /opt/nester/setup-secrets.sh << 'SETUPEOF'
#!/bin/bash
# Fetch API keys from Secrets Manager and update .env
# Requires AWS credentials to be configured first
set -e
cd /opt/nester
REGION="{region}"
API_KEYS_SECRET_ARN="{self.api_keys_secret_arn}"

if ! aws sts get-caller-identity &>/dev/null; then
    echo "ERROR: AWS credentials not configured."
    echo "Run 'aws configure' with credentials from:"
    echo "  aws secretsmanager get-secret-value --secret-id {self.ecr_credentials_secret_arn} --region {region}"
    exit 1
fi

echo "Fetching API keys from Secrets Manager..."
SECRET_JSON=$(aws secretsmanager get-secret-value --secret-id "$API_KEYS_SECRET_ARN" --region "$REGION" --query SecretString --output text)

if [ -z "$SECRET_JSON" ] || [ "$SECRET_JSON" == "null" ]; then
    echo "ERROR: Could not fetch secrets"
    exit 1
fi

# Append secrets to .env (skip placeholders)
echo "" >> .env
echo "# API Keys from Secrets Manager" >> .env
echo "$SECRET_JSON" | python3 -c "
import sys, json
try:
    secrets = json.load(sys.stdin)
    for key, value in secrets.items():
        if not str(value).startswith('PLACEHOLDER_'):
            print(f'{{key}}={{value}}')
except Exception as e:
    print(f'Error: {{e}}', file=sys.stderr)
    sys.exit(1)
" >> .env

echo "Secrets configured successfully!"
echo "Run './deploy.sh' to start the service"
SETUPEOF
chmod +x /opt/nester/setup-secrets.sh
chown ec2-user:ec2-user /opt/nester/setup-secrets.sh

# ============================================
# STEP 6: Systemd service (for auto-start after reboot)
# NOTE: First deployment requires manual setup, but reboots will auto-start
# ============================================
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

# ============================================
# STEP 7: Create helper scripts
# ============================================
cat > /opt/nester/deploy.sh << 'DEPLOYEOF'
#!/bin/bash
set -e
cd /opt/nester

# Verify AWS credentials
if ! aws sts get-caller-identity &>/dev/null; then
    echo "ERROR: AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi

# Verify .env has API keys
if ! grep -q "GOOGLE_API_KEY=" .env 2>/dev/null || grep -q "PLACEHOLDER_" .env 2>/dev/null; then
    echo "WARNING: .env may be missing API keys. Run './setup-secrets.sh' first."
fi

echo "Logging into ECR..."
./ecr-login.sh

echo "Pulling latest images..."
docker compose pull

echo "Starting containers..."
docker compose up -d --force-recreate

echo ""
echo "Deployment complete!"
docker compose ps
DEPLOYEOF
chmod +x /opt/nester/deploy.sh
chown ec2-user:ec2-user /opt/nester/deploy.sh

cat > /opt/nester/logs.sh << 'LOGSEOF'
#!/bin/bash
cd /opt/nester
docker compose logs -f "$@"
LOGSEOF
chmod +x /opt/nester/logs.sh
chown ec2-user:ec2-user /opt/nester/logs.sh

cat > /opt/nester/status.sh << 'STATUSEOF'
#!/bin/bash
cd /opt/nester
echo "=== Container Status ==="
docker compose ps
echo ""
echo "=== Recent Logs ==="
docker compose logs --tail=20
STATUSEOF
chmod +x /opt/nester/status.sh
chown ec2-user:ec2-user /opt/nester/status.sh

cat > /opt/nester/refresh-env.sh << 'REFRESHEOF'
#!/bin/bash
# Refresh environment variables from Secrets Manager
set -e
cd /opt/nester
REGION="{region}"
API_KEYS_SECRET_ARN="{self.api_keys_secret_arn}"

if ! aws sts get-caller-identity &>/dev/null; then
    echo "ERROR: AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi

echo "Fetching latest secrets..."
SECRET_JSON=$(aws secretsmanager get-secret-value --secret-id "$API_KEYS_SECRET_ARN" --region "$REGION" --query SecretString --output text)

# Backup old .env
cp .env .env.backup

# Recreate .env with server config
cat > .env << 'ENVEOF'
# Auto-generated environment file
# Server Configuration
{chr(10).join(f'{k}={v}' for k, v in env_vars.items())}
ENVEOF

# Append secrets
echo "" >> .env
echo "# API Keys from Secrets Manager" >> .env
echo "$SECRET_JSON" | python3 -c "
import sys, json
try:
    secrets = json.load(sys.stdin)
    for key, value in secrets.items():
        if not str(value).startswith('PLACEHOLDER_'):
            print(f'{{key}}={{value}}')
except:
    pass
" >> .env

echo "Environment refreshed. Restart containers with: docker compose up -d --force-recreate"
REFRESHEOF
chmod +x /opt/nester/refresh-env.sh
chown ec2-user:ec2-user /opt/nester/refresh-env.sh

# Set ownership for all files
chown -R ec2-user:ec2-user /opt/nester

echo "========================================="
echo "NesterAI instance setup complete!"
echo "HTTPS enabled: {'yes' if use_https else 'no'}"
echo "========================================="
echo ""
echo "MANUAL SETUP REQUIRED (one-time):"
echo "1. SSH to instance"
echo "2. Run: aws configure"
echo "   (Get credentials from nester/dev/ecr-credentials secret)"
echo "3. Run: /opt/nester/setup-secrets.sh"
echo "4. Run: /opt/nester/deploy.sh"
echo ""
echo "Helper scripts:"
echo "  /opt/nester/setup-secrets.sh - Fetch API keys from Secrets Manager"
echo "  /opt/nester/deploy.sh        - Pull and restart containers"
echo "  /opt/nester/logs.sh          - View container logs"
echo "  /opt/nester/status.sh        - Check container status"
echo "  /opt/nester/refresh-env.sh   - Refresh secrets from AWS"
"""
        return user_data

    def _generate_http_compose(self, app) -> str:
        """Generate docker-compose for HTTP-only mode."""
        return f"""services:
  backend:
    image: {self.backend_image_uri}
    container_name: nester-backend
    restart: always
    ports:
      - "{app.server.fastapi_port}:{app.server.fastapi_port}"
    env_file:
      - .env
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{app.server.fastapi_port}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    networks:
      - nester-network

  frontend:
    image: {self.frontend_image_uri}
    container_name: nester-frontend
    restart: always
    ports:
      - "80:80"
    environment:
      - BACKEND_URL=http://localhost:{app.server.fastapi_port}
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:80/"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - nester-network

networks:
  nester-network:
    driver: bridge"""

    def _generate_https_compose(self, app) -> str:
        """Generate docker-compose with Caddy for HTTPS."""
        return f"""services:
  # Caddy - Reverse Proxy with automatic HTTPS
  caddy:
    image: caddy:2-alpine
    container_name: nester-caddy
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - nester-network

  backend:
    image: {self.backend_image_uri}
    container_name: nester-backend
    restart: always
    expose:
      - "{app.server.fastapi_port}"
    env_file:
      - .env
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{app.server.fastapi_port}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    networks:
      - nester-network

  frontend:
    image: {self.frontend_image_uri}
    container_name: nester-frontend
    restart: always
    expose:
      - "80"
    environment:
      - BACKEND_URL=https://{app.domain.name}
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:80/"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - nester-network

networks:
  nester-network:
    driver: bridge

volumes:
  caddy_data:
  caddy_config:"""

    def _generate_caddyfile(self, app) -> str:
        """Generate Caddyfile creation script for HTTPS."""
        domain = app.domain.name
        backend_port = app.server.fastapi_port

        return f"""# Create Caddyfile for HTTPS
cat > /opt/nester/Caddyfile << 'CADDYEOF'
# Automatic HTTPS with Caddy for {domain}

{domain} {{
    # API endpoints
    handle /health* {{
        reverse_proxy backend:{backend_port}
    }}

    handle /connect* {{
        reverse_proxy backend:{backend_port}
    }}

    handle /status* {{
        reverse_proxy backend:{backend_port}
    }}

    # A2UI and Graph endpoints
    handle /a2ui/* {{
        reverse_proxy backend:{backend_port}
    }}

    handle /graph/* {{
        reverse_proxy backend:{backend_port}
    }}

    # API docs
    handle /docs* {{
        reverse_proxy backend:{backend_port}
    }}

    handle /openapi.json {{
        reverse_proxy backend:{backend_port}
    }}

    # WebSocket support
    handle /ws* {{
        reverse_proxy backend:{backend_port}
    }}

    # Frontend - default handler (must be last)
    handle {{
        reverse_proxy frontend:80
    }}

    encode gzip
}}
CADDYEOF

# Add redirect from IP-based nip.io domain (for backwards compatibility)
INSTANCE_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "")
if [ -n "$INSTANCE_IP" ] && [ "{domain}" != "$INSTANCE_IP.nip.io" ]; then
    cat >> /opt/nester/Caddyfile << REDIRECTEOF

# Redirect old nip.io to new domain
$INSTANCE_IP.nip.io {{
    redir https://{domain}{{uri}} permanent
}}
REDIRECTEOF
fi
echo "Caddyfile created for {domain}"
"""