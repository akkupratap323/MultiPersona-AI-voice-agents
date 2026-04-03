"""
VoiceAI - Voice Assistant Application

A production-ready voice AI assistant built with Pipecat framework,
featuring RAG capabilities, real-time speech processing, and WebSocket communication.

Project Structure:
    app/
    ├── api/           - FastAPI routes and WebSocket handlers
    ├── config/        - Configuration management
    ├── core/          - Voice assistant and server logic
    ├── models/        - Pydantic data models
    ├── services/      - Service implementations (STT, TTS, RAG, etc.)
    └── utils/         - Utility functions and helpers
"""

__version__ = "1.0.0"
__author__ = "Voice AI"
__all__ = ["__version__", "__author__"]
