"""
Pydantic schemas for API requests and responses.

This module defines all data models used for API communication.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConnectionRequest(BaseModel):
    """Request model for establishing a voice connection."""

    session_id: Optional[str] = Field(None, description="Optional session ID for tracking")
    config: Optional[Dict[str, Any]] = Field(None, description="Optional configuration overrides")


class ConnectionResponse(BaseModel):
    """Response model for connection establishment."""

    websocket_url: str = Field(..., description="WebSocket URL for voice communication")
    session_id: str = Field(..., description="Assigned session ID")
    status: str = Field(default="ready", description="Connection status")


class StatusResponse(BaseModel):
    """Response model for server status."""

    status: str = Field(..., description="Server status")
    active_sessions: int = Field(default=0, description="Number of active sessions")
    uptime_seconds: float = Field(default=0.0, description="Server uptime in seconds")
    version: str = Field(default="1.0.0", description="Application version")
    config: Optional[Dict[str, Any]] = Field(None, description="Current configuration")


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    services: Optional[Dict[str, str]] = Field(None, description="Individual service statuses")


class RAGQueryRequest(BaseModel):
    """Request model for RAG queries."""

    query: str = Field(..., min_length=1, description="User query text")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to retrieve")
    mode: str = Field(default="mix", description="Query mode: mix, local, global, hybrid")


class RAGQueryResponse(BaseModel):
    """Response model for RAG queries."""

    answer: str = Field(..., description="Generated answer")
    relevance_score: float = Field(default=0.0, description="Relevance score of the answer")
    sources: List[str] = Field(default_factory=list, description="Source documents used")
    query: str = Field(..., description="Original query")


class LatencyMetrics(BaseModel):
    """Model for latency metrics reporting."""

    interaction_id: str = Field(..., description="Unique interaction identifier")
    stt_latency_ms: float = Field(default=0.0, description="Speech-to-text latency in ms")
    llm_latency_ms: float = Field(default=0.0, description="LLM processing latency in ms")
    tts_latency_ms: float = Field(default=0.0, description="Text-to-speech latency in ms")
    total_latency_ms: float = Field(default=0.0, description="Total end-to-end latency in ms")
    voice_to_voice_latency_ms: float = Field(
        default=0.0, description="Voice-to-voice response time in ms"
    )
    timestamps: Optional[Dict[str, float]] = Field(None, description="Detailed timestamps")


class WebSocketMessage(BaseModel):
    """Model for WebSocket message communication."""

    type: str = Field(..., description="Message type")
    payload: Optional[Dict[str, Any]] = Field(None, description="Message payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class AppointmentBookingRequest(BaseModel):
    """Request model for appointment booking."""

    first_name: str = Field(..., min_length=1, max_length=100, description="User's first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="User's last name")
    email: str = Field(
        ...,
        pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        description="User's email address"
    )
    submitted_by: str = Field(default="Nester AI", description="Source of submission")


class AppointmentBookingResponse(BaseModel):
    """Response model for appointment booking."""

    success: bool = Field(..., description="Whether the booking was successful")
    message: Optional[str] = Field(None, description="Success message")
    error: Optional[str] = Field(None, description="Error message if booking failed")
