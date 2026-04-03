#!/usr/bin/env python3
"""
NesterAI Infrastructure CDK Application.

This is the entry point for the AWS CDK application.

Usage:
    # Deploy dev environment (default)
    cdk deploy

    # Synthesize CloudFormation template
    cdk synth

    # Compare deployed stack with current state
    cdk diff
"""

import os
import aws_cdk as cdk

from stacks.lightsail_stack import LightsailStack
from utils.config_loader import ConfigLoader


def main():
    app = cdk.App()

    # Get environment from context (defaults to dev)
    environment = app.node.try_get_context("environment") or "dev"

    # Load configuration for the specified environment
    config_loader = ConfigLoader()
    config = config_loader.load(environment)

    # Get AWS account and region from environment or config
    account = os.environ.get("CDK_DEFAULT_ACCOUNT") or config.aws.account_id
    region = os.environ.get("CDK_DEFAULT_REGION") or config.aws.region

    if not account:
        print("Warning: AWS account not specified. Set CDK_DEFAULT_ACCOUNT or configure in YAML.")
        print("You can also run: aws sts get-caller-identity --query Account --output text")

    # Create the Lightsail infrastructure stack
    LightsailStack(
        app,
        f"NesterAI-Lightsail-{environment.capitalize()}",
        config=config,
        env=cdk.Environment(
            account=account,
            region=region,
        ),
        description=f"NesterAI Voice Assistant - Lightsail Infrastructure ({environment})",
    )

    # Synthesize the app
    app.synth()


if __name__ == "__main__":
    main()