"""
Lightsail Infrastructure Stack for NesterAI Voice Assistant.

Deploys a Lightsail instance with Docker containers for the voice assistant.
Uses Custom Resources to work around CloudFormation Lightsail limitations.
"""

from constructs import Construct
from aws_cdk import (
    Stack,
    CfnOutput,
    Tags,
    aws_iam as iam,
)

from utils.config_loader import NesterConfig
from components import (
    NesterSecrets,
    NesterECR,
)
from components.ecr_credentials import EcrCredentials
from components.lightsail_custom import LightsailCustomResource


class LightsailStack(Stack):
    """
    Lightsail infrastructure stack for NesterAI Voice Assistant.

    Creates:
    - ECR repositories for container images
    - Secrets Manager secret for API keys
    - Lightsail instance with Docker setup
    - Static IP for consistent endpoint
    - IAM role for Lightsail to access Secrets Manager and ECR
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        config: NesterConfig,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.config = config

        # Apply tags to all resources in this stack
        for key, value in config.tags.items():
            Tags.of(self).add(key, value)
        Tags.of(self).add("Environment", config.environment)
        Tags.of(self).add("Stack", id)

        # 1. Create ECR repositories for container images
        self.ecr = NesterECR(
            self,
            "ECR",
            config=config,
        )

        # 2. Create Secrets Manager secret for API keys
        self.secrets = NesterSecrets(
            self,
            "Secrets",
            config=config,
        )

        # 3. Create IAM user and credentials for ECR access
        # (Lightsail doesn't support IAM instance roles, so we use stored credentials)
        self.ecr_credentials = EcrCredentials(
            self,
            "EcrCredentials",
            config=config,
            backend_repo_arn=self.ecr.backend_repo.repository_arn,
            frontend_repo_arn=self.ecr.frontend_repo.repository_arn,
        )

        # 4. Create Lightsail instance with Static IP using Custom Resource
        # (Uses SDK calls to bypass CloudFormation Lightsail limitations)
        self.lightsail = LightsailCustomResource(
            self,
            "Lightsail",
            config=config,
            api_keys_secret_arn=self.secrets.secret_arn,
            ecr_credentials_secret_arn=self.ecr_credentials.secret_arn,
            backend_image_uri=self.ecr.backend_image_uri(config.image_tag),
            frontend_image_uri=self.ecr.frontend_image_uri(config.image_tag),
        )

        # Stack outputs
        CfnOutput(
            self,
            "SecretArn",
            value=self.secrets.secret_arn,
            description="ARN of the Secrets Manager secret containing API keys",
            export_name=f"{config.resource_prefix}-secret-arn",
        )

        CfnOutput(
            self,
            "SecretName",
            value=self.secrets.secret_name,
            description="Name of the Secrets Manager secret",
        )

        CfnOutput(
            self,
            "InstanceName",
            value=self.lightsail.instance_name,
            description="Lightsail instance name",
        )

        if config.lightsail.static_ip.enabled:
            CfnOutput(
                self,
                "StaticIpAddress",
                value=self.lightsail.ip_address,
                description="Static IP address of the Lightsail instance",
                export_name=f"{config.resource_prefix}-static-ip",
            )

            CfnOutput(
                self,
                "ApplicationUrl",
                value=f"http://{self.lightsail.ip_address}",
                description="URL to access the application (update with domain if configured)",
            )

            CfnOutput(
                self,
                "SshCommand",
                value=f"ssh -i ~/.ssh/LightsailDefaultKey-{config.aws.region}.pem ec2-user@{self.lightsail.ip_address}",
                description="SSH command to connect to the instance",
            )

        CfnOutput(
            self,
            "UpdateSecretsCommand",
            value=f"aws secretsmanager put-secret-value --secret-id {self.secrets.secret_name} --secret-string file://secrets.json --region {config.aws.region}",
            description="Command to update secrets (create secrets.json with your API keys first)",
        )

        # ECR outputs for CI/CD integration
        CfnOutput(
            self,
            "BackendEcrRepoUri",
            value=self.ecr.backend_repo_uri,
            description="ECR repository URI for backend image (use in CI/CD)",
            export_name=f"{config.resource_prefix}-backend-ecr-uri",
        )

        CfnOutput(
            self,
            "FrontendEcrRepoUri",
            value=self.ecr.frontend_repo_uri,
            description="ECR repository URI for frontend image (use in CI/CD)",
            export_name=f"{config.resource_prefix}-frontend-ecr-uri",
        )

        CfnOutput(
            self,
            "EcrLoginCommand",
            value=f"aws ecr get-login-password --region {config.aws.region} | docker login --username AWS --password-stdin {self.ecr.backend_repo_uri.split('/')[0]}",
            description="Command to authenticate Docker with ECR",
        )