"""
Speech-to-Text service for the Voice Assistant.

This module provides speech-to-text functionality using various STT engines
including Whisper and Deepgram, with support for text normalization and
noise filtering.
"""

import re
import unicodedata
from typing import Any, Dict, List, Tuple

from deepgram import LiveOptions
from loguru import logger
from pipecat.frames.frames import Frame, TranscriptionFrame
from pipecat.processors.frame_processor import FrameDirection
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.whisper.stt import WhisperSTTService
from pipecat.transcriptions.language import Language


class TextNormalizedDeepgramSTTService(DeepgramSTTService):
    """Deepgram STT service with Unicode normalization and config-driven STT corrections.

    Extends the base Deepgram STT service to:
    - Normalize Unicode text, preventing JSON encoding issues
    - Apply configurable post-processing corrections for STT misrecognitions

    Corrections are loaded from config.yaml `stt.config.corrections` as a list of
    {"pattern": "regex", "replacement": "text"} entries, compiled once at init time.
    """

    def __init__(self, api_key: str, live_options: LiveOptions = None,
                 corrections: List[Dict] = None, **kwargs):
        """Initialize the normalized Deepgram STT service.

        Args:
            api_key: Deepgram API key
            live_options: Deepgram live options configuration
            corrections: List of {"pattern": "regex", "replacement": "text"} dicts
            **kwargs: Additional arguments for the base service
        """
        super().__init__(api_key=api_key, live_options=live_options, **kwargs)
        self._corrections: List[Tuple[re.Pattern, str]] = []
        if corrections:
            for entry in corrections:
                try:
                    compiled = re.compile(entry["pattern"], re.IGNORECASE)
                    self._corrections.append((compiled, entry["replacement"]))
                except (re.error, KeyError) as e:
                    logger.warning(f"Invalid STT correction entry {entry}: {e}")
            logger.info(f"STT post-processing: {len(self._corrections)} corrections loaded")

    def _normalize_text(self, text: str) -> str:
        """Normalize Unicode text to prevent encoding issues.

        Args:
            text: Input text to normalize

        Returns:
            Normalized text string
        """
        if not text:
            return text

        try:
            # Normalize to NFC form (canonical decomposition, then composition)
            normalized = unicodedata.normalize("NFC", text)
            return normalized.encode("utf-8").decode("utf-8")
        except (UnicodeError, TypeError) as e:
            logger.warning(f"Text normalization failed for '{text}': {e}")
            return text

    def _apply_corrections(self, text: str) -> str:
        """Apply config-driven STT corrections to transcribed text.

        Args:
            text: Transcribed text that may contain misrecognitions

        Returns:
            Text with corrections applied
        """
        if not text or not self._corrections:
            return text
        for pattern, replacement in self._corrections:
            text = pattern.sub(replacement, text)
        return text

    async def push_frame(self, frame: Frame, direction: FrameDirection = FrameDirection.DOWNSTREAM) -> None:
        """Override push_frame to normalize text and fix proper nouns.

        Args:
            frame: Frame to push
            direction: Frame direction
        """
        # Log and normalize TranscriptionFrames
        if isinstance(frame, TranscriptionFrame):
            logger.info(f"🎤 STT push_frame: TranscriptionFrame text='{frame.text}'")
            if frame.text:
                corrected = self._apply_corrections(self._normalize_text(frame.text))
                if corrected != frame.text:
                    logger.debug(f"STT corrected: '{frame.text}' -> '{corrected}'")
                    frame = TranscriptionFrame(
                        text=corrected,
                        user_id=frame.user_id,
                        timestamp=frame.timestamp,
                        language=getattr(frame, "language", None),
                    )

        await super().push_frame(frame, direction)

    async def queue_frame(self, frame: Frame, direction: FrameDirection = FrameDirection.DOWNSTREAM) -> None:
        """Override queue_frame to log transcription frames.

        Args:
            frame: Frame to queue
            direction: Frame direction
        """
        # Log TranscriptionFrames
        if isinstance(frame, TranscriptionFrame):
            logger.info(f"🎤 STT queue_frame: TranscriptionFrame text='{frame.text}'")

        await super().queue_frame(frame, direction)


class SpeechToTextService:
    """Service for converting speech to text.

    Provides a unified interface for speech-to-text functionality using
    different STT providers (Whisper, Deepgram).

    Attributes:
        stt_provider: Name of the STT provider
        stt_service: Underlying STT service instance
        config: Configuration dictionary
    """

    def __init__(self, stt_provider: str = "whisper", **kwargs):
        """Initialize the Speech-to-Text service.

        Args:
            stt_provider: STT provider ("whisper" or "deepgram")
            **kwargs: Additional configuration parameters
        """
        self.stt_provider = stt_provider
        self.stt_service = None
        self.config = kwargs

    def initialize(self) -> Any:
        """Initialize the STT service based on the provider.

        Returns:
            Initialized STT service instance

        Raises:
            ValueError: If provider is unsupported or API key is missing
        """
        if self.stt_provider == "whisper":
            self.stt_service = WhisperSTTService(
                device=self.config.get("device", "cpu"),
                model=self.config.get("model", "small"),
                no_speech_prob=self.config.get("no_speech_prob", 0.3),
            )
        elif self.stt_provider == "deepgram":
            api_key = self.config.get("api_key")
            if not api_key:
                raise ValueError("Deepgram API key is required")

            language = self.config.get("language", "en")
            detect_language = self.config.get("detect_language", False)

            live_options_config = {
                "model": self.config.get("model", "nova-2"),
                "smart_format": self.config.get("smart_format", True),
                "filler_words": self.config.get("filler_words", False),
                "punctuate": self.config.get("punctuate", True),
                "endpointing": self.config.get("endpointing", 500),
                "utterance_end_ms": self.config.get("utterance_end_ms", 1200),
                "interim_results": self.config.get("interim_results", True),
                # CRITICAL: Disable Deepgram VAD events to prevent false interruptions
                # The local Silero VAD handles speech detection with tuned parameters
                # Deepgram VAD was causing bot to be cut off on deployed version
                "vad_events": self.config.get("vad_events", False),
            }

            # NOTE: Deepgram's `keywords` param breaks Nova-3 WebSocket connections.
            # Proper noun correction is handled via config-driven post-processing
            # in TextNormalizedDeepgramSTTService._apply_corrections() instead.
            corrections = self.config.get("corrections", [])

            if detect_language:
                live_options_config["detect_language"] = True
            elif language == "multi" or language == "hi" or self.config.get("support_hinglish", False):
                # Multi-language mode: Hindi + English (Hinglish) support via Deepgram Nova-3
                live_options_config["language"] = "multi"
            else:
                language_mapping = {"en": Language.EN, "hi": Language.HI}
                live_options_config["language"] = language_mapping.get(language, Language.EN)

            live_options = LiveOptions(**live_options_config)
            logger.info(
                f"Deepgram LiveOptions: smart_format={live_options_config['smart_format']}, "
                f"endpointing={live_options_config['endpointing']}ms"
            )

            self.stt_service = TextNormalizedDeepgramSTTService(
                api_key=api_key, live_options=live_options, corrections=corrections
            )
        else:
            raise ValueError(f"Unsupported STT provider: {self.stt_provider}")

        logger.info(f"Initialized STT service: {self.stt_provider}")
        return self.stt_service

    def get_service(self) -> Any:
        """Get the STT service instance, initializing if needed.

        Returns:
            STT service instance
        """
        if self.stt_service is None:
            self.initialize()
        return self.stt_service

    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration.

        Returns:
            Configuration dictionary
        """
        return {"provider": self.stt_provider, "config": self.config}

    def update_config(self, **kwargs) -> None:
        """Update configuration and reinitialize if needed.

        Args:
            **kwargs: New configuration parameters
        """
        self.config.update(kwargs)
        logger.info(f"Updated STT config: {kwargs}")

        if self.stt_service is not None:
            logger.info("Re-initializing STT service with new config")
            self.initialize()
