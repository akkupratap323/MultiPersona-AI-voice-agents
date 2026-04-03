"""Smart Interruption Processor with Context Validation.

This processor validates interruptions to prevent false barge-ins from:
- Background conversations not directed at the bot
- Random environmental noise
- TV/music/other speakers

It warns users about background noise when detected.
"""

import time
from typing import Optional
from loguru import logger

from pipecat.frames.frames import (
    Frame,
    TranscriptionFrame,
    TTSSpeakFrame,
    CancelFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
    StartFrame,
    AudioRawFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


class SmartInterruptionProcessor(FrameProcessor):
    """Validates interruptions to filter out background noise.

    Features:
    - Detects if speech is directed at the bot (context validation)
    - Warns user about background noise
    - Prevents false interruptions during bot speech
    """

    def __init__(
        self,
        enabled: bool = True,
        min_confidence_threshold: float = 0.7,
        context_keywords: Optional[list] = None,
    ):
        """Initialize smart interruption processor.

        Args:
            enabled: Enable smart interruption filtering
            min_confidence_threshold: Minimum confidence to accept interruption
            context_keywords: Keywords that indicate user is talking to bot
        """
        super().__init__()
        self.enabled = enabled
        self._min_confidence = min_confidence_threshold

        # Default context keywords (bot name, greetings, commands)
        self._context_keywords = context_keywords or [
            "hey", "hello", "hi", "nester", "assistant", "bot",
            "help", "please", "tell me", "what", "how", "can you",
            "show me", "explain", "stop", "wait", "hold on"
        ]

        # State tracking
        self._bot_is_speaking = False
        self._last_transcription = ""
        self._last_warning_time = 0.0
        self._warning_cooldown = 10.0  # Warn max once per 10 seconds
        self._consecutive_background_noise = 0

        logger.info(
            f"SmartInterruptionProcessor initialized: enabled={enabled}, "
            f"confidence_threshold={min_confidence_threshold}"
        )

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process frames and validate interruptions.

        Args:
            frame: Frame to process
            direction: Direction of frame flow
        """
        # Pass through StartFrame and AudioRawFrame immediately (we only process transcriptions)
        if isinstance(frame, (StartFrame, AudioRawFrame)):
            await self.push_frame(frame, direction)
            return

        # Track when bot starts/stops speaking
        if isinstance(frame, TTSSpeakFrame):
            self._bot_is_speaking = True

        # Track user speech
        if isinstance(frame, UserStartedSpeakingFrame):
            if self._bot_is_speaking and self.enabled:
                logger.debug("User started speaking while bot is talking - checking context")

        if isinstance(frame, UserStoppedSpeakingFrame):
            # Reset state when user stops
            pass

        # Validate transcription for interruptions
        if isinstance(frame, TranscriptionFrame):
            text = frame.text.strip().lower()

            if text and self._bot_is_speaking:
                # User is speaking while bot is talking - validate if it's an interruption
                is_valid_interruption = self._is_valid_interruption(text)

                if not is_valid_interruption:
                    # Background noise detected - warn user and don't interrupt
                    logger.warning(
                        f"🔇 Background noise detected (not interruption): '{text}'"
                    )

                    self._consecutive_background_noise += 1

                    # Warn user after multiple background noise detections
                    if self._consecutive_background_noise >= 2:
                        await self._warn_user_about_noise()
                        self._consecutive_background_noise = 0

                    # Don't pass this transcription downstream (prevents false interruption)
                    return
                else:
                    # Valid interruption - allow it
                    logger.info(f"✅ Valid interruption detected: '{text}'")
                    self._bot_is_speaking = False
                    self._consecutive_background_noise = 0

            self._last_transcription = text

        # Detect when bot finishes speaking (CancelFrame or silence)
        if isinstance(frame, CancelFrame):
            self._bot_is_speaking = False

        # Always pass frame downstream
        await self.push_frame(frame, direction)

    def _is_valid_interruption(self, text: str) -> bool:
        """Check if speech is a valid interruption or background noise.

        Args:
            text: Transcribed text (lowercase)

        Returns:
            True if valid interruption, False if background noise
        """
        if not self.enabled:
            return True  # Always allow if disabled

        # Check 1: Contains context keywords (talking to bot)
        contains_context = any(keyword in text for keyword in self._context_keywords)

        # Check 2: Is a question (starts with what/how/why/when/where/who)
        is_question = any(text.startswith(q) for q in ["what", "how", "why", "when", "where", "who", "can you"])

        # Check 3: Is a command (contains action verbs)
        command_verbs = ["stop", "wait", "hold", "pause", "cancel", "tell", "show", "explain"]
        is_command = any(verb in text for verb in command_verbs)

        # Valid if any condition is met
        is_valid = contains_context or is_question or is_command

        logger.debug(
            f"Interruption validation: '{text}' -> "
            f"context={contains_context}, question={is_question}, "
            f"command={is_command} => {'VALID' if is_valid else 'BACKGROUND'}"
        )

        return is_valid

    async def _warn_user_about_noise(self):
        """Warn user about background noise interfering with conversation."""
        current_time = time.time()

        # Only warn if enough time has passed since last warning
        if current_time - self._last_warning_time < self._warning_cooldown:
            return

        self._last_warning_time = current_time

        # Emit warning message to user
        warning_text = (
            "I'm detecting some background noise. "
            "For the best experience, please reduce background sounds."
        )

        logger.warning(f"⚠️ Warning user about background noise")

        # Create TTS frame to speak the warning
        warning_frame = TTSSpeakFrame(text=warning_text)
        await self.push_frame(warning_frame, FrameDirection.DOWNSTREAM)
