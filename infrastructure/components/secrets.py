"""
Secrets Manager construct for NesterAI API keys.

Uses L2 constructs (fully supported) for AWS Secrets Manager.
"""

import json
from constructs import Construct
from aws_cdk import (
    RemovalPolicy,
    aws_secretsmanager as secretsmanager,
)

from utils.config_loader import NesterConfig


class NesterSecrets(Construct):
    """
    Creates and manages AWS Secrets Manager secrets for NesterAI.

    Creates a single secret with multiple key-value pairs for all API keys.
    Values are placeholders - update via AWS Console or CLI after deployment.

    IMPORTANT: Once created, CDK will NOT overwrite your secret values.
    Manual updates via CLI/Console are preserved across deployments.
    The generate_secret_string only runs on CREATE, not on UPDATE.
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        config: NesterConfig,
    ) -> None:
        super().__init__(scope, id)

        self.config = config
        env = config.environment
        prefix = config.secrets.name_prefix

        # Build initial secret structure with placeholder values
        # These are ONLY used on first creation - updates preserve existing values
        secret_object: dict[str, str] = {}
        for api_key in config.secrets.api_keys:
            # Use descriptive placeholder that indicates the key needs to be set
            placeholder = f"PLACEHOLDER_{api_key.name}_SET_VIA_CONSOLE"
            secret_object[api_key.name] = placeholder

        # Create the secret with generate_secret_string
        # CloudFormation only generates/sets values on CREATE, not on UPDATE
        # So manual updates via CLI/Console are preserved
        self.api_keys_secret = secretsmanager.Secret(
            self,
            "ApiKeysSecret",
            secret_name=f"{prefix}/{env}/api-keys",
            description=f"API keys for NesterAI Voice Assistant ({env})",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps(secret_object),
                generate_string_key="ROTATION_TOKEN",  # Dummy key, not used
                exclude_punctuation=True,
            ),
            removal_policy=RemovalPolicy.RETAIN,  # Don't delete secrets on stack destroy
        )

        # Store ARN for reference
        self.secret_arn = self.api_keys_secret.secret_arn
        self.secret_name = self.api_keys_secret.secret_name

    def _dict_to_json(self, d: dict[str, str]) -> str:
        """Convert dict to JSON string."""
        import json
        return json.dumps(d)

    def get_secret_value_reference(self, key_name: str) -> str:
        """
        Get the ARN reference for a specific key in the secret.

        Use this for ECS task definitions or other services that need
        to reference individual secret values.
        """
        return f"{self.secret_arn}:{key_name}::"

    def grant_read(self, grantee) -> None:
        """Grant read access to the secret."""
        self.api_keys_secret.grant_read(grantee)