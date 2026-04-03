"""
Configuration loader for NesterAI Infrastructure.

Loads base configuration and merges with environment-specific overrides.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class PortConfig(BaseModel):
    port: int
    protocol: str = "tcp"
    cidrs: list[str] = Field(default_factory=list)


class LightsailInstanceConfig(BaseModel):
    bundle_id: str = "medium_3_0"
    blueprint_id: str = "amazon_linux_2023"
    availability_zone_suffix: str = "a"


class LightsailNetworkingConfig(BaseModel):
    ports: list[PortConfig] = Field(default_factory=list)


class StaticIpConfig(BaseModel):
    enabled: bool = True


class LightsailConfig(BaseModel):
    instance: LightsailInstanceConfig = Field(default_factory=LightsailInstanceConfig)
    static_ip: StaticIpConfig = Field(default_factory=StaticIpConfig)
    networking: LightsailNetworkingConfig = Field(
        default_factory=LightsailNetworkingConfig
    )


class AwsConfig(BaseModel):
    region: str = "us-west-2"
    account_id: str | None = None


class ProjectConfig(BaseModel):
    name: str = "nester-ai"
    description: str = "NesterAI Voice Assistant Infrastructure"


class ApiKeyConfig(BaseModel):
    name: str
    description: str = ""
    required: bool = False


class SecretsConfig(BaseModel):
    name_prefix: str = "nester"
    api_keys: list[ApiKeyConfig] = Field(default_factory=list)


class ServerConfig(BaseModel):
    fastapi_host: str = "0.0.0.0"
    fastapi_port: int = 7860
    websocket_host: str = "0.0.0.0"
    websocket_port: int = 8765
    session_timeout: int = 180
    log_level: str = "INFO"


class DockerConfig(BaseModel):
    """Docker/container configuration. ECR repositories created by CDK."""
    image_tag: str = "latest"


class DomainConfig(BaseModel):
    name: str = ""
    use_https: bool = True


class ApplicationConfig(BaseModel):
    server: ServerConfig = Field(default_factory=ServerConfig)
    docker: DockerConfig = Field(default_factory=DockerConfig)
    domain: DomainConfig = Field(default_factory=DomainConfig)


class AlarmsConfig(BaseModel):
    cpu_threshold: int = 80
    memory_threshold: int = 80


class MonitoringConfig(BaseModel):
    enabled: bool = True
    log_retention_days: int = 30
    alarms: AlarmsConfig = Field(default_factory=AlarmsConfig)


class NesterConfig(BaseModel):
    """Complete configuration for NesterAI infrastructure."""

    environment: str = "staging"
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    aws: AwsConfig = Field(default_factory=AwsConfig)
    lightsail: LightsailConfig = Field(default_factory=LightsailConfig)
    secrets: SecretsConfig = Field(default_factory=SecretsConfig)
    application: ApplicationConfig = Field(default_factory=ApplicationConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    tags: dict[str, str] = Field(default_factory=dict)

    @property
    def resource_prefix(self) -> str:
        """Generate resource name prefix."""
        return f"{self.project.name}-{self.environment}"

    @property
    def availability_zone(self) -> str:
        """Full availability zone."""
        return f"{self.aws.region}{self.lightsail.instance.availability_zone_suffix}"

    @property
    def image_tag(self) -> str:
        """Container image tag."""
        return self.application.docker.image_tag


class ConfigLoader:
    """Load and merge configuration from YAML files."""

    def __init__(self, config_dir: str | Path | None = None):
        if config_dir is None:
            # Default to config directory relative to this file
            config_dir = Path(__file__).parent.parent / "config"
        self.config_dir = Path(config_dir)

    def _load_yaml(self, filename: str) -> dict[str, Any]:
        """Load a YAML file."""
        filepath = self.config_dir / filename
        if not filepath.exists():
            return {}
        with open(filepath) as f:
            return yaml.safe_load(f) or {}

    def _deep_merge(
        self, base: dict[str, Any], override: dict[str, Any]
    ) -> dict[str, Any]:
        """Deep merge two dictionaries, with override taking precedence."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def load(self, environment: str = "staging") -> NesterConfig:
        """
        Load configuration for the specified environment.

        Loads base.yaml first, then merges with environment-specific config.
        """
        # Load base configuration
        base_config = self._load_yaml("base.yaml")

        # Load environment-specific configuration
        env_config = self._load_yaml(f"{environment}.yaml")

        # Merge configurations
        merged_config = self._deep_merge(base_config, env_config)

        # Ensure environment is set
        merged_config["environment"] = environment

        # Create and validate config
        return NesterConfig(**merged_config)


def get_config(environment: str = "staging") -> NesterConfig:
    """Convenience function to load configuration."""
    loader = ConfigLoader()
    return loader.load(environment)