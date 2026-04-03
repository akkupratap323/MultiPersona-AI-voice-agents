"""
Services module containing all voice assistant service implementations.

This module provides:
- Speech-to-Text (STT) service
- Text-to-Speech (TTS) service
- RAG (Retrieval Augmented Generation) service with A2UI support
- Conversation management
- Input analysis
- Latency monitoring
- A2UI visual generation services
"""

from app.services.stt import SpeechToTextService
from app.services.tts import TextToSpeechService
from app.services.rag import RAGService, LightRAGService, A2UIResponse, create_rag_service
from app.services.conversation import ConversationManager
from app.services.input_analyzer import InputAnalyzer
from app.services.latency import LatencyAnalyzer

__all__ = [
    "SpeechToTextService",
    "TextToSpeechService",
    "RAGService",
    "LightRAGService",
    "A2UIResponse",
    "create_rag_service",
    "ConversationManager",
    "InputAnalyzer",
    "LatencyAnalyzer",
]
