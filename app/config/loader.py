"""
Configuration loader for YAML-based configuration with environment variable substitution.

This module provides backward compatibility with the existing YAML configuration
while supporting the new Pydantic-based settings.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Union

import yaml
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv(override=True)


def _substitute_env_vars(config: Union[Dict, list, str]) -> Union[Dict, list, str]:
    """Recursively substitute environment variables in configuration.

    Args:
        config: Configuration object (dict, list, or string)

    Returns:
        Configuration with environment variables substituted
    """
    if isinstance(config, dict):
        return {key: _substitute_env_vars(value) for key, value in config.items()}
    elif isinstance(config, list):
        return [_substitute_env_vars(item) for item in config]
    elif isinstance(config, str):
        # Pattern to match ${VAR_NAME} or ${VAR_NAME:default_value}
        pattern = r"\$\{([^}]+)\}"
        matches = re.findall(pattern, config)

        result = config
        for match in matches:
            var_name = match
            default_value = ""

            # Check if there's a default value specified
            if ":" in match:
                var_name, default_value = match.split(":", 1)

            # Get environment variable value
            env_value = os.getenv(var_name, default_value)

            # Replace the placeholder with the actual value
            result = result.replace(f"${{{match}}}", env_value)

        return result
    else:
        return config


def load_config(config_file: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file.

    Args:
        config_file: Path to the YAML configuration file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If the config file doesn't exist
        yaml.YAMLError: If the YAML file is malformed
    """
    # Try multiple locations for config file
    possible_paths = [
        Path(__file__).parent / config_file,
        Path(__file__).parent.parent / "config" / config_file,
        Path.cwd() / "config" / config_file,
        Path.cwd() / config_file,
    ]

    config_path = None
    for path in possible_paths:
        if path.exists():
            config_path = path
            break

    if config_path is None:
        raise FileNotFoundError(
            f"Configuration file not found. Searched in: {[str(p) for p in possible_paths]}"
        )

    logger.debug(f"Loading configuration from: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Substitute environment variables
    config = _substitute_env_vars(config)

    return config


def get_assistant_config() -> Dict[str, Any]:
    """Get configuration for the Voice Assistant.

    Returns:
        Configuration dictionary for all services

    Raises:
        FileNotFoundError: If the config file doesn't exist
        yaml.YAMLError: If the YAML file is malformed
        ValueError: If required environment variables are missing
    """
    config = load_config()

    # Validate that required API keys are set
    required_keys = [
        ("tts.config.api_key", config.get("tts", {}).get("config", {}).get("api_key")),
        (
            "conversation.llm.api_key",
            config.get("conversation", {}).get("llm", {}).get("api_key"),
        ),
    ]

    # Check for voice config based on TTS provider
    tts_provider = config.get("tts", {}).get("provider", "deepgram")
    if tts_provider == "elevenlabs":
        required_keys.append(
            ("tts.config.voice_id", config.get("tts", {}).get("config", {}).get("voice_id"))
        )

    missing_keys = []
    for key_path, value in required_keys:
        if not value or value.startswith("${"):
            missing_keys.append(key_path)

    if missing_keys:
        raise ValueError(
            f"Missing required environment variables for: {', '.join(missing_keys)}. "
            f"Please check your .env file and config.yaml"
        )

    return config
