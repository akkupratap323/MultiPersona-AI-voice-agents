"""
Helper functions for the NesterVoiceAI application.

This module provides common utility functions used throughout the application.
"""

import json
import time
import uuid
from typing import Any, Dict, Optional


def generate_session_id(prefix: str = "session") -> str:
    """Generate a unique session ID.

    Args:
        prefix: Prefix for the session ID

    Returns:
        Unique session identifier string
    """
    timestamp = int(time.time() * 1000)
    unique_id = uuid.uuid4().hex[:8]
    return f"{prefix}_{timestamp}_{unique_id}"


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Human-readable duration string
    """
    if seconds < 0.001:
        return f"{seconds * 1000000:.2f}us"
    elif seconds < 1:
        return f"{seconds * 1000:.2f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        return f"{hours}h {remaining_minutes}m"


def safe_json_loads(data: str, default: Optional[Any] = None) -> Any:
    """Safely parse JSON string with fallback.

    Args:
        data: JSON string to parse
        default: Default value if parsing fails

    Returns:
        Parsed JSON data or default value
    """
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else {}


def merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries.

    Args:
        base: Base dictionary
        override: Dictionary with override values

    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to append if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def normalize_text(text: str) -> str:
    """Normalize text for consistent processing.

    Args:
        text: Text to normalize

    Returns:
        Normalized text
    """
    import unicodedata

    # Normalize Unicode characters
    text = unicodedata.normalize("NFKC", text)
    # Remove extra whitespace
    text = " ".join(text.split())
    return text.strip()
