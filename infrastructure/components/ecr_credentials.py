"""
ECR Credentials for Lightsail instance and CI/CD.

Creates an IAM user with ECR pull/push permissions and stores
credentials in Secrets Manager. Used by:
- Lightsail instance for pulling images
- GitHub Actions for building and pushing images
"""

from constructs import Construct
from aws_cdk import (
    SecretValue,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
)

from utils.config_loader import NesterConfig


class EcrCredentials(Construct):
    """
    Creates IAM credentials for ECR access from Lightsail.

    Lightsail instances don't support IAM instance roles like EC2,
    so we create an IAM user with access keys stored in Secrets Manager.
    The instance fetches these credentials and configures AWS CLI.
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        config: NesterConfig,
        backend_repo_arn: str,
        frontend_repo_arn: str,
    ) -> None:
        super().__init__(scope, id)

        self.config = config
        prefix = config.resource_prefix

        # Create IAM user for ECR access (pull for Lightsail, push for CI/CD)
        self.ecr_user = iam.User(
            self,
            "EcrUser",
            user_name=f"{prefix}-ecr-user",
        )

        # Grant ECR authentication (required for both pull and push)
        self.ecr_user.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ecr:GetAuthorizationToken",
                ],
                resources=["*"],
            )
        )

        # Grant ECR pull permissions (for Lightsail instance)
        self.ecr_user.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                ],
                resources=[backend_repo_arn, frontend_repo_arn],
            )
        )

        # Grant ECR push permissions (for CI/CD)
        self.ecr_user.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ecr:InitiateLayerUpload",
                    "ecr:UploadLayerPart",
                    "ecr:CompleteLayerUpload",
                    "ecr:PutImage",
                ],
                resources=[backend_repo_arn, frontend_repo_arn],
            )
        )

        # Also grant Secrets Manager read access (for API keys)
        self.ecr_user.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret",
                ],
                resources=[f"arn:aws:secretsmanager:{config.aws.region}:*:secret:{config.secrets.name_prefix}/*"],
            )
        )

        # Create access key for the user
        self.access_key = iam.AccessKey(
            self,
            "EcrPullAccessKey",
            user=self.ecr_user,
        )

        # Store credentials in Secrets Manager
        self.credentials_secret = secretsmanager.Secret(
            self,
            "EcrCredentialsSecret",
            secret_name=f"{config.secrets.name_prefix}/{config.environment}/ecr-credentials",
            description=f"AWS credentials for ECR access from Lightsail ({config.environment})",
            secret_object_value={
                "AWS_ACCESS_KEY_ID": SecretValue.unsafe_plain_text(self.access_key.access_key_id),
                "AWS_SECRET_ACCESS_KEY": self.access_key.secret_access_key,
                "AWS_REGION": SecretValue.unsafe_plain_text(config.aws.region),
            },
        )

    @property
    def secret_arn(self) -> str:
        """ARN of the credentials secret."""
        return self.credentials_secret.secret_arn

    @property
    def secret_name(self) -> str:
        """Name of the credentials secret."""
        return self.credentials_secret.secret_name