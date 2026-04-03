"""
Pytest configuration and fixtures for NesterVoiceAI tests.
"""

import os
import pytest
from typing import Dict, Any

# Set test environment
os.environ["TESTING"] = "true"


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Provide sample configuration for tests."""
    return {
        "language": {
            "primary": "en",
            "support_hinglish": False,
            "auto_detect": False,
        },
        "stt": {
            "provider": "deepgram",
            "config": {
                "model": "nova-2",
                "api_key": "test_key",
                "language": "en",
            },
        },
        "tts": {
            "provider": "deepgram",
            "config": {
                "api_key": "test_key",
                "voice": "aura-asteria-en",
            },
        },
        "rag": {
            "type": "mock",
            "config": {},
        },
        "conversation": {
            "llm": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "api_key": "test_key",
            },
        },
        "server": {
            "websocket_host": "127.0.0.1",
            "websocket_port": 8765,
            "fastapi_host": "127.0.0.1",
            "fastapi_port": 7860,
            "session_timeout": 180,
            "vad": {
                "confidence": 0.88,
                "start_secs": 0.35,
                "stop_secs": 0.5,
                "min_volume": 0.78,
            },
        },
    }


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    monkeypatch.setenv("DEEPGRAM_API_KEY", "test_deepgram_key")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
