"""
Application settings using Pydantic for validation and environment variable loading.

This module provides a centralized configuration management system that:
- Loads settings from environment variables
- Validates configuration values
- Provides type-safe access to settings
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class ServerSettings(BaseSettings):
    """Server configuration settings."""

    fastapi_host: str = Field(default="0.0.0.0", description="FastAPI server host")
    fastapi_port: int = Field(default=7860, description="FastAPI server port")
    websocket_host: str = Field(default="0.0.0.0", description="WebSocket server host")
    websocket_port: int = Field(default=8765, description="WebSocket server port")
    session_timeout: int = Field(default=180, description="Session timeout in seconds")
    public_url: Optional[str] = Field(default=None, description="Public URL for production")

    class Config:
        env_prefix = ""
        case_sensitive = False


class DeepgramSettings(BaseSettings):
    """Deepgram API configuration."""

    api_key: str = Field(default="", description="Deepgram API key")
    stt_model: str = Field(default="nova-2", description="STT model")
    tts_voice: str = Field(default="aura-asteria-en", description="TTS voice")
    language: str = Field(default="en", description="Language code")

    class Config:
        env_prefix = "DEEPGRAM_"
        case_sensitive = False


class OpenAISettings(BaseSettings):
    """OpenAI API configuration."""

    api_key: str = Field(default="", description="OpenAI API key")
    model: str = Field(default="gpt-3.5-turbo", description="LLM model")

    class Config:
        env_prefix = "OPENAI_"
        case_sensitive = False


class ElevenLabsSettings(BaseSettings):
    """ElevenLabs API configuration."""

    api_key: str = Field(default="", description="ElevenLabs API key")
    voice_id: str = Field(default="", description="Voice ID")

    class Config:
        env_prefix = "ELEVENLABS_"
        case_sensitive = False


class PineconeSettings(BaseSettings):
    """Pinecone vector database configuration."""

    api_key: str = Field(default="", description="Pinecone API key")
    index: str = Field(default="voice-assistant-rag", description="Index name")

    class Config:
        env_prefix = "PINECONE_"
        case_sensitive = False


class RAGSettings(BaseSettings):
    """RAG service configuration."""

    type: str = Field(default="lightrag", description="RAG service type")
    api_url: str = Field(default="https://lightragnl.duckdns.org", description="LightRAG API URL")
    mode: str = Field(default="local", description="Query mode")
    top_k: int = Field(default=3, description="Number of results to retrieve")
    timeout: int = Field(default=20, description="API timeout in seconds")

    class Config:
        env_prefix = "RAG_"
        case_sensitive = False


class VADSettings(BaseSettings):
    """Voice Activity Detection settings."""

    confidence: float = Field(default=0.85, ge=0.5, le=0.95, description="VAD confidence threshold")
    start_secs: float = Field(default=0.3, description="Seconds of speech to start")
    stop_secs: float = Field(default=0.6, description="Seconds of silence to stop")
    min_volume: float = Field(default=0.75, ge=0.5, le=0.9, description="Minimum volume threshold")

    class Config:
        env_prefix = "VAD_"
        case_sensitive = False


class Settings(BaseSettings):
    """Main application settings aggregating all configuration sections."""

    # Application metadata
    app_name: str = Field(default="NesterVoiceAI", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Sub-configurations
    server: ServerSettings = Field(default_factory=ServerSettings)
    deepgram: DeepgramSettings = Field(default_factory=DeepgramSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    elevenlabs: ElevenLabsSettings = Field(default_factory=ElevenLabsSettings)
    pinecone: PineconeSettings = Field(default_factory=PineconeSettings)
    rag: RAGSettings = Field(default_factory=RAGSettings)
    vad: VADSettings = Field(default_factory=VADSettings)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: Application settings instance
    """
    return Settings()
