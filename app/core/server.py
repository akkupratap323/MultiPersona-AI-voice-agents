"""
Voice Assistant Server for handling WebSocket connections.

This module provides the server infrastructure for running the voice assistant,
including WebSocket transport management and session handling.
"""

import asyncio
import os
from typing import Any, Dict

from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.serializers.protobuf import ProtobufFrameSerializer
from pipecat.transports.websocket.server import (
    WebsocketServerParams,
    WebsocketServerTransport,
)

from app.core.voice_assistant import VoiceAssistant


class VoiceAssistantServer:
    """Voice Assistant server with WebSocket support.

    Supports multiple connect/disconnect cycles without server restart.

    Attributes:
        config: Server configuration dictionary
        server_config: Server-specific configuration
        voice_assistant: Current voice assistant instance
        websocket_server_transport: WebSocket transport instance
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the Voice Assistant server.

        Args:
            config: Configuration dictionary for the voice assistant and server
        """
        self.config = config or {}
        self.server_config = self.config.get("server", {})
        self._apply_server_defaults()
        self.voice_assistant = None
        self.websocket_server_transport = None
        self._running = True

        logger.info("Initialized Voice Assistant Server")

    def _apply_server_defaults(self) -> None:
        """Apply default server configuration values from environment."""
        defaults = {
            "fastapi_host": os.getenv("FASTAPI_HOST", "0.0.0.0"),
            "fastapi_port": int(os.getenv("FASTAPI_PORT", "7860")),
            "websocket_host": os.getenv("WEBSOCKET_HOST", "0.0.0.0"),
            "websocket_port": int(os.getenv("WEBSOCKET_PORT", "8765")),
            "session_timeout": int(os.getenv("SESSION_TIMEOUT", "180")),
            "audio_in_enabled": os.getenv("AUDIO_IN_ENABLED", "true").lower() == "true",
            "audio_out_enabled": os.getenv("AUDIO_OUT_ENABLED", "true").lower() == "true",
            "add_wav_header": os.getenv("ADD_WAV_HEADER", "false").lower() == "true",
            "vad": {},
        }

        for key, value in defaults.items():
            if key not in self.server_config:
                self.server_config[key] = value

    def create_websocket_transport(self) -> WebsocketServerTransport:
        """Create and configure the standalone WebSocket transport.

        Returns:
            Configured WebSocket transport for standalone server
        """
        host = self.server_config.get("websocket_host", "0.0.0.0")
        port = self.server_config.get("websocket_port", 8765)
        session_timeout = self.server_config.get("session_timeout", 180)
        audio_in_enabled = self.server_config.get("audio_in_enabled", True)
        audio_out_enabled = self.server_config.get("audio_out_enabled", True)
        add_wav_header = self.server_config.get("add_wav_header", False)

        # Create VAD analyzer with noise-resistant settings
        vad_config = self.server_config.get("vad", {})
        vad_params = VADParams(
            confidence=vad_config.get("confidence", 0.85),
            start_secs=vad_config.get("start_secs", 0.3),
            stop_secs=vad_config.get("stop_secs", 0.6),
            min_volume=vad_config.get("min_volume", 0.75),
        )
        vad_analyzer = SileroVADAnalyzer(params=vad_params)
        logger.info(
            f"VAD configured: confidence={vad_params.confidence}, "
            f"min_volume={vad_params.min_volume}, start_secs={vad_params.start_secs}"
        )

        # Create transport parameters
        # Note: host and port must be passed directly to WebsocketServerTransport
        # Get TTS sample rate from config (Resemble=24kHz, ElevenLabs=24kHz, default=16kHz)
        tts_config = self.config.get("tts", {}).get("config", {})
        audio_out_sample_rate = tts_config.get("sample_rate", 16000)
        logger.info(f"Transport audio_out_sample_rate={audio_out_sample_rate}")

        transport_params = WebsocketServerParams(
            serializer=ProtobufFrameSerializer(),
            audio_in_enabled=audio_in_enabled,
            audio_out_enabled=audio_out_enabled,
            audio_out_sample_rate=audio_out_sample_rate,
            add_wav_header=add_wav_header,
            vad_analyzer=vad_analyzer,
            session_timeout=session_timeout,
        )

        self.websocket_server_transport = WebsocketServerTransport(
            params=transport_params,
            host=host,
            port=port,
        )

        logger.info(f"Created standalone WebSocket transport on {host}:{port}")
        return self.websocket_server_transport

    async def run_websocket_server(self) -> None:
        """Run the standalone WebSocket server with reconnection support.

        This method runs in a loop to allow multiple client connections
        without needing to restart the server.
        """
        logger.info("Starting standalone Voice Assistant WebSocket Server...")

        while self._running:
            try:
                # Create fresh voice assistant for each session
                voice_assistant = VoiceAssistant(self.config)

                # Create fresh transport for each session
                transport = self.create_websocket_transport()

                logger.info("Voice Assistant ready for new connection...")

                # Run the voice assistant with the transport
                await voice_assistant.run(transport, handle_sigint=False)

            except asyncio.CancelledError:
                logger.info("WebSocket server task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket Server session: {e}")
                await asyncio.sleep(1)
                logger.info("Restarting voice assistant for new connections...")
                continue

            logger.info("Session ended, ready for new connection...")
            await asyncio.sleep(0.5)

    def get_server_status(self) -> Dict[str, Any]:
        """Get the status of the server and voice assistant.

        Returns:
            Dictionary containing server status and configuration
        """
        status = {
            "server": {
                "mode": os.getenv("WEBSOCKET_SERVER", "fast_api"),
                "config": self.server_config,
            }
        }

        if hasattr(self, "voice_assistant") and self.voice_assistant:
            if hasattr(self.voice_assistant, "get_service_status"):
                status["voice_assistant"] = self.voice_assistant.get_service_status()

        return status

    def stop(self) -> None:
        """Stop the server gracefully."""
        self._running = False
        logger.info("Server stop requested")


# Global server instance
voice_assistant_server = VoiceAssistantServer()
