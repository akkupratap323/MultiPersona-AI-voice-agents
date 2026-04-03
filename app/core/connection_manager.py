"""
Connection Manager for handling multiple concurrent WebSocket sessions.

This module provides session tracking, capacity management, and heartbeat
monitoring for multiple simultaneous voice assistant connections.
"""

import asyncio
from typing import Dict, Optional
from fastapi import WebSocket, status
from loguru import logger


class ConnectionManager:
    """Manages multiple concurrent WebSocket connections with capacity limits.

    Features:
    - Track active sessions by session ID
    - Enforce maximum concurrent connection limit
    - Heartbeat monitoring to detect stale connections
    - Automatic cleanup on disconnect
    - VAD analyzer registry for runtime parameter changes
    """

    def __init__(self, max_sessions: int = 20):
        """Initialize the Connection Manager.

        Args:
            max_sessions: Maximum number of concurrent sessions (default 20 for Lightsail)
        """
        self.active_sessions: Dict[str, WebSocket] = {}
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}
        self.vad_analyzers: Dict[str, any] = {}  # session_id -> SileroVADAnalyzer
        self.max_sessions = max_sessions
        logger.info(f"ConnectionManager initialized with max_sessions={max_sessions}")

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        """Accept and register a new WebSocket connection.

        Args:
            websocket: FastAPI WebSocket connection
            session_id: Unique session identifier

        Raises:
            WebSocketException: If maximum session capacity is reached
        """
        # Check capacity
        if len(self.active_sessions) >= self.max_sessions:
            logger.warning(
                f"Session {session_id} rejected: capacity reached "
                f"({len(self.active_sessions)}/{self.max_sessions})"
            )
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason=f"Server at capacity ({self.max_sessions} sessions)"
            )
            return

        # Accept connection
        await websocket.accept()
        self.active_sessions[session_id] = websocket
        logger.info(
            f"[Session {session_id}] Connected. "
            f"Active sessions: {len(self.active_sessions)}/{self.max_sessions}"
        )

        # Start heartbeat monitoring
        heartbeat_task = asyncio.create_task(self._heartbeat(websocket, session_id))
        self.heartbeat_tasks[session_id] = heartbeat_task

    def register_vad_analyzer(self, session_id: str, vad_analyzer) -> None:
        """Register a VAD analyzer for a session (enables runtime param changes).

        Args:
            session_id: Session identifier
            vad_analyzer: SileroVADAnalyzer instance
        """
        self.vad_analyzers[session_id] = vad_analyzer

    def get_vad_analyzer(self, session_id: str):
        """Get the VAD analyzer for a session.

        Args:
            session_id: Session identifier

        Returns:
            SileroVADAnalyzer instance or None
        """
        return self.vad_analyzers.get(session_id)

    def disconnect(self, session_id: str) -> None:
        """Unregister a WebSocket connection and cleanup resources.

        Args:
            session_id: Session identifier to disconnect
        """
        # Cancel heartbeat task
        if session_id in self.heartbeat_tasks:
            self.heartbeat_tasks[session_id].cancel()
            del self.heartbeat_tasks[session_id]

        # Remove VAD analyzer
        self.vad_analyzers.pop(session_id, None)

        # Remove from active sessions
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(
                f"[Session {session_id}] Disconnected. "
                f"Active sessions: {len(self.active_sessions)}/{self.max_sessions}"
            )

    async def _heartbeat(self, websocket: WebSocket, session_id: str) -> None:
        """Send periodic heartbeat pings to detect stale connections.

        Sends a ping every 30 seconds. If connection is dropped, automatically
        cleans up the session.

        Args:
            websocket: WebSocket connection to monitor
            session_id: Session identifier for cleanup
        """
        try:
            while True:
                await asyncio.sleep(30)  # 30 second interval
                try:
                    # Send ping frame
                    await websocket.send_json({"type": "ping", "timestamp": asyncio.get_event_loop().time()})
                    logger.debug(f"[Session {session_id}] Heartbeat ping sent")
                except Exception as e:
                    logger.warning(f"[Session {session_id}] Heartbeat failed: {e}")
                    # Connection is dead, clean up
                    self.disconnect(session_id)
                    break
        except asyncio.CancelledError:
            logger.debug(f"[Session {session_id}] Heartbeat task cancelled")
        except Exception as e:
            logger.error(f"[Session {session_id}] Heartbeat error: {e}")
            self.disconnect(session_id)

    def get_active_session_count(self) -> int:
        """Get the number of currently active sessions.

        Returns:
            Number of active sessions
        """
        return len(self.active_sessions)

    def get_session_ids(self) -> list:
        """Get list of all active session IDs.

        Returns:
            List of active session IDs
        """
        return list(self.active_sessions.keys())

    def is_session_active(self, session_id: str) -> bool:
        """Check if a session is currently active.

        Args:
            session_id: Session identifier to check

        Returns:
            True if session is active, False otherwise
        """
        return session_id in self.active_sessions


# Global connection manager instance
connection_manager = ConnectionManager(max_sessions=20)
