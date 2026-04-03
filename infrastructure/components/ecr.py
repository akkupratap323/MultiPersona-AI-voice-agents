"""
ECR Repository construct for NesterAI container images.

Uses L2 constructs (fully supported) for AWS ECR.
"""

from constructs import Construct
from aws_cdk import (
    Duration,
    RemovalPolicy,
    aws_ecr as ecr,
)

from utils.config_loader import NesterConfig


class NesterECR(Construct):
    """
    Creates ECR repositories for NesterAI container images.

    Creates separate repositories for backend and frontend images.
    Repository names: {project}-{environment}-backend/frontend
    Example: nester-ai-staging-backend, nester-ai-staging-frontend
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        config: NesterConfig,
    ) -> None:
        super().__init__(scope, id)

        self.config = config
        prefix = config.resource_prefix  # e.g., "nester-ai-staging"

        # Backend repository
        self.backend_repo = ecr.Repository(
            self,
            "BackendRepo",
            repository_name=f"{prefix}-backend",
            removal_policy=RemovalPolicy.RETAIN,  # Keep images on stack destroy
            image_scan_on_push=True,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    description="Delete untagged images older than 7 days",
                    max_image_age=Duration.days(7),
                    tag_status=ecr.TagStatus.UNTAGGED,
                    rule_priority=1,
                ),
                ecr.LifecycleRule(
                    description="Keep last 10 images",
                    max_image_count=10,
                    rule_priority=2,  # ANY rules must have highest priority number
                ),
            ],
        )

        # Frontend repository
        self.frontend_repo = ecr.Repository(
            self,
            "FrontendRepo",
            repository_name=f"{prefix}-frontend",
            removal_policy=RemovalPolicy.RETAIN,
            image_scan_on_push=True,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    description="Delete untagged images older than 7 days",
                    max_image_age=Duration.days(7),
                    tag_status=ecr.TagStatus.UNTAGGED,
                    rule_priority=1,
                ),
                ecr.LifecycleRule(
                    description="Keep last 10 images",
                    max_image_count=10,
                    rule_priority=2,  # ANY rules must have highest priority number
                ),
            ],
        )

    @property
    def backend_repo_uri(self) -> str:
        """Full URI for backend repository."""
        return self.backend_repo.repository_uri

    @property
    def frontend_repo_uri(self) -> str:
        """Full URI for frontend repository."""
        return self.frontend_repo.repository_uri

    def backend_image_uri(self, tag: str = "latest") -> str:
        """Get full image URI with tag for backend."""
        return f"{self.backend_repo_uri}:{tag}"

    def frontend_image_uri(self, tag: str = "latest") -> str:
        """Get full image URI with tag for frontend."""
        return f"{self.frontend_repo_uri}:{tag}"