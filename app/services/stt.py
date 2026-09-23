"""
Speech-to-Text service for the Voice Assistant.

This module provides speech-to-text functionality using various STT engines
including Whisper and Deepgram, with support for text normalization and
noise filtering.
"""

import re
import unicodedata
from typing import Any, Dict, List, Tuple

from loguru import logger
from pipecat.frames.frames import Frame, TranscriptionFrame
from pipecat.processors.frame_processor import FrameDirection
from pipecat.services.deepgram.flux.stt import DeepgramFluxSTTService
from pipecat.transcriptions.language import Language


class TextNormalizedDeepgramFluxSTTService(DeepgramFluxSTTService):
    """Deepgram STT service with Unicode normalization and config-driven STT corrections.

    Extends the base Deepgram STT service to:
    - Normalize Unicode text, preventing JSON encoding issues
    - Apply configurable post-processing corrections for STT misrecognitions

    Corrections are loaded from config.yaml `stt.config.corrections` as a list of
    {"pattern": "regex", "replacement": "text"} entries, compiled once at init time.
    """

    def __init__(self, api_key: str, corrections: List[Dict] = None, **kwargs):
        """Initialize the normalized Deepgram STT service.

        Args:
            api_key: Deepgram API key
            corrections: List of {"pattern": "regex", "replacement": "text"} dicts
            **kwargs: Additional arguments for the base service
        """
        super().__init__(api_key=api_key, **kwargs)
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
            from pipecat.services.whisper.stt import WhisperSTTService

            self.stt_service = WhisperSTTService(
                device=self.config.get("device", "cpu"),
                model=self.config.get("model", "small"),
                no_speech_prob=self.config.get("no_speech_prob", 0.3),
            )
        elif self.stt_provider in {"deepgram", "deepgram_flux"}:
            api_key = self.config.get("api_key")
            if not api_key:
                raise ValueError("Deepgram API key is required")

            language = self.config.get("language", "en")
            corrections = self.config.get("corrections", [])
            multilingual = (
                language in {"multi", "hi"}
                or self.config.get("detect_language", False)
                or self.config.get("support_hinglish", False)
            )
            model = "flux-general-multi" if multilingual else self.config.get(
                "model", "flux-general-en"
            )
            language_hints = [Language.EN, Language.HI] if multilingual else None
            settings = DeepgramFluxSTTService.Settings(
                model=model,
                language_hints=language_hints,
                eot_threshold=self.config.get("eot_threshold", 0.7),
                eot_timeout_ms=self.config.get("eot_timeout_ms", 5000),
                min_confidence=self.config.get("min_confidence", 0.3),
                keyterm=self.config.get("keyterms", []),
                numerals=self.config.get("numerals", True),
            )
            logger.info(
                f"Deepgram Flux: model={model}, "
                f"eot_threshold={settings.eot_threshold}, "
                f"eot_timeout_ms={settings.eot_timeout_ms}"
            )

            self.stt_service = TextNormalizedDeepgramFluxSTTService(
                api_key=api_key,
                corrections=corrections,
                settings=settings,
                sample_rate=self.config.get("sample_rate", 16000),
                should_interrupt=True,
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
