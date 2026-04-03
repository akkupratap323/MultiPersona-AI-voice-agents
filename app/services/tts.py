"""
Text-to-Speech service for the Voice Assistant.

This module provides text-to-speech functionality using various TTS engines
including Deepgram, ElevenLabs, Cartesia, and Chatterbox (Resemble AI).
"""

from typing import Any, Dict

from loguru import logger
from pipecat.frames.frames import TTSSpeakFrame
from pipecat.services.cartesia.tts import CartesiaTTSService, GenerationConfig
from pipecat.services.deepgram.tts import DeepgramTTSService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService

from app.services.chatterbox_tts import ChatterboxTTSService


class TextToSpeechService:
    """Service for converting text to speech.

    Provides a unified interface for text-to-speech functionality using
    different TTS providers.

    Attributes:
        tts_provider: Name of the TTS provider
        tts_service: Underlying TTS service instance
        config: Configuration dictionary
    """

    def __init__(self, tts_provider: str = "deepgram", **kwargs):
        """Initialize the Text-to-Speech service.

        Args:
            tts_provider: TTS provider ("deepgram", "elevenlabs", or "cartesia")
            **kwargs: Additional configuration parameters
        """
        self.tts_provider = tts_provider
        self.tts_service = None
        self.config = kwargs

    def initialize(self) -> Any:
        """Initialize the TTS service based on the provider.

        Returns:
            Initialized TTS service instance

        Raises:
            ValueError: If provider is unsupported or required config is missing
        """
        if self.tts_provider == "deepgram":
            api_key = self.config.get("api_key")
            if not api_key:
                raise ValueError("Deepgram API key is required")

            # Support both 'model' (Nova 3) and 'voice' (Aura) parameters
            model = self.config.get("model")
            voice = self.config.get("voice", "aura-asteria-en")
            encoding = self.config.get("encoding", "linear16")
            sample_rate = self.config.get("sample_rate", 24000)

            # Use model if provided, otherwise use voice
            voice_or_model = model if model else voice

            self.tts_service = DeepgramTTSService(
                api_key=api_key,
                voice=voice_or_model,
                encoding=encoding,
                sample_rate=sample_rate
            )
            logger.info(f"Using Deepgram TTS - model: {voice_or_model}, encoding: {encoding}, sample_rate: {sample_rate}Hz")

        elif self.tts_provider == "elevenlabs":
            api_key = self.config.get("api_key")
            voice_id = self.config.get("voice_id")

            if not api_key:
                raise ValueError("ElevenLabs API key is required")
            if not voice_id:
                raise ValueError("ElevenLabs voice ID is required")

            support_hinglish = self.config.get("support_hinglish", False)
            hinglish_voice_id = self.config.get("hinglish_voice_id")

            if support_hinglish and hinglish_voice_id:
                selected_voice_id = hinglish_voice_id
                logger.info("Using Hinglish voice for TTS")
            else:
                selected_voice_id = voice_id
                logger.info(f"Using configured voice for TTS")

            # Get model and latency optimization settings
            model_id = self.config.get("model_id", "eleven_turbo_v2_5")
            optimize_latency = self.config.get("optimize_streaming_latency", 4)
            output_format = self.config.get("output_format", "pcm_16000")

            self.tts_service = ElevenLabsTTSService(
                api_key=api_key,
                voice_id=selected_voice_id,
                model=model_id,  # Use turbo model for lowest latency
                optimize_streaming_latency=optimize_latency,  # Maximum optimization
                output_format=output_format,  # Raw PCM for lowest latency
            )
            logger.info(f"Using ElevenLabs TTS with model: {model_id}, latency optimization: {optimize_latency}")

        elif self.tts_provider == "cartesia":
            api_key = self.config.get("api_key")
            voice_id = self.config.get("voice_id")

            if not api_key:
                raise ValueError("Cartesia API key is required")
            if not voice_id:
                raise ValueError("Cartesia voice ID is required")

            support_hinglish = self.config.get("support_hinglish", False)
            hinglish_voice_id = self.config.get("hinglish_voice_id")

            if support_hinglish and hinglish_voice_id:
                selected_voice_id = hinglish_voice_id
            else:
                selected_voice_id = voice_id

            model = self.config.get("model", "sonic-3")
            initial_emotion = self.config.get("emotion", "neutral")

            generation_config = GenerationConfig(emotion=initial_emotion)
            params = CartesiaTTSService.InputParams(generation_config=generation_config)

            self.tts_service = CartesiaTTSService(
                api_key=api_key,
                voice_id=selected_voice_id,
                model=model,
                params=params,
            )
            logger.info(f"Using Cartesia TTS model={model} voice_id={selected_voice_id} emotion={initial_emotion}")

        elif self.tts_provider == "chatterbox":
            api_key = self.config.get("api_key")
            voice_uuid = self.config.get("voice_uuid")
            if not api_key:
                raise ValueError("Resemble AI API key is required for Chatterbox")
            if not voice_uuid:
                raise ValueError("Resemble AI voice UUID is required for Chatterbox")

            synthesis_url = self.config.get("synthesis_url", "https://f.cluster.resemble.ai/synthesize")
            stream_url = self.config.get("stream_url", "https://f.cluster.resemble.ai/stream")
            sample_rate = self.config.get("sample_rate", 24000)
            model = self.config.get("model", "chatterbox-turbo")
            voice = self.config.get("voice", "neutral")

            self.tts_service = ChatterboxTTSService(
                api_key=api_key,
                voice_uuid=voice_uuid,
                synthesis_url=synthesis_url,
                stream_url=stream_url,
                sample_rate=sample_rate,
                model=model,
                voice=voice,
            )
            logger.info(f"Using Chatterbox TTS model={model} (voice_uuid={voice_uuid}, sample_rate={sample_rate}Hz)")

        else:
            raise ValueError(f"Unsupported TTS provider: {self.tts_provider}")

        logger.info(f"Initialized TTS service: {self.tts_provider}")
        return self.tts_service

    def get_service(self) -> Any:
        """Get the TTS service instance, initializing if needed.

        Returns:
            TTS service instance
        """
        if self.tts_service is None:
            self.initialize()
        return self.tts_service

    async def speak_text(self, text: str) -> None:
        """Convert text to speech and queue for playback.

        Args:
            text: Text to convert to speech

        Raises:
            Exception: If speech synthesis fails
        """
        if self.tts_service is None:
            self.initialize()

        try:
            await self.tts_service.queue_frame(TTSSpeakFrame(text))
            logger.info(f"Queued speech: {text[:50]}...")
        except Exception as e:
            logger.error(f"Failed to queue speech: {e}")
            raise

    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration.

        Returns:
            Configuration dictionary
        """
        return {"provider": self.tts_provider, "config": self.config}

    def update_config(self, **kwargs) -> None:
        """Update configuration and reinitialize if needed.

        Args:
            **kwargs: New configuration parameters
        """
        self.config.update(kwargs)
        logger.info(f"Updated TTS config: {kwargs}")

        if self.tts_service is not None:
            logger.info("Re-initializing TTS service with new config")
            self.initialize()

    def get_voice_settings(self) -> Dict[str, Any]:
        """Get current voice settings.

        Returns:
            Voice settings dictionary
        """
        return {
            "provider": self.tts_provider,
            "voice_id": self.config.get("voice_id"),
            "api_key_configured": bool(self.config.get("api_key")),
        }
