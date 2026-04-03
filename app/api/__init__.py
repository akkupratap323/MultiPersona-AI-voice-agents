"""API module containing FastAPI routes and WebSocket handlers."""

from app.api.routes import router
from app.api.websocket import websocket_endpoint

__all__ = ["router", "websocket_endpoint"]
