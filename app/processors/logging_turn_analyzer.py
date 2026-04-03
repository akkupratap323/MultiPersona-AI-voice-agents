"""
Logging wrapper for SmartTurn v3 analyzer.

This module wraps the LocalSmartTurnAnalyzerV3 to add detailed logging
for debugging and monitoring end-of-turn detection.
"""

from typing import Optional, Tuple
from loguru import logger

# Import the base class and types for proper interface compliance
from pipecat.audio.turn.base_turn_analyzer import BaseTurnAnalyzer, EndOfTurnState
from pipecat.metrics.metrics import MetricsData


class LoggingSmartTurnAnalyzer(BaseTurnAnalyzer):
    """Wrapper around LocalSmartTurnAnalyzerV3 that adds logging.

    This wrapper logs:
    - When audio is appended for analysis
    - When end-of-turn analysis is performed
    - The result of end-of-turn detection
    - Statistics about audio processing

    It inherits from BaseTurnAnalyzer to ensure compatibility with
    pipecat's transport layer validation.
    """

    def __init__(self, cpu_count: int = 1, session_id: str = "unknown"):
        """Initialize the logging wrapper.

        Args:
            cpu_count: Number of CPU threads for ONNX inference
            session_id: Session ID for logging context
        """
        # Don't call super().__init__() as BaseTurnAnalyzer is abstract
        # and we're delegating to the inner analyzer
        from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3

        logger.info(f"[Session {session_id}] 🧠 Creating LocalSmartTurnAnalyzerV3...")
        self._analyzer = LocalSmartTurnAnalyzerV3(cpu_count=cpu_count)
        self._session_id = session_id
        self._audio_chunks_received = 0
        self._analysis_count = 0
        self._end_of_turn_detections = 0
        self._speech_chunks = 0
        self._last_logged_speech_triggered = False  # Track state changes

        logger.info(f"[Session {session_id}] " + "=" * 50)
        logger.info(f"[Session {session_id}] 🧠 SMARTTURN V3 WRAPPER READY")
        logger.info(f"[Session {session_id}]    ├─ Wrapper: LoggingSmartTurnAnalyzer")
        logger.info(f"[Session {session_id}]    ├─ Inner: LocalSmartTurnAnalyzerV3")
        logger.info(f"[Session {session_id}]    ├─ CPU threads: {cpu_count}")
        logger.info(f"[Session {session_id}]    └─ Logging: Audio chunks, analyses, end-of-turn events")
        logger.info(f"[Session {session_id}] " + "=" * 50)

    @property
    def params(self):
        """Get analyzer params."""
        return self._analyzer.params

    @property
    def sample_rate(self) -> int:
        """Get sample rate."""
        return self._analyzer.sample_rate

    @property
    def speech_triggered(self) -> bool:
        """Check if speech has been triggered."""
        return self._analyzer.speech_triggered

    def set_sample_rate(self, sample_rate: int):
        """Set the sample rate."""
        logger.info(f"[Session {self._session_id}] 🧠 SmartTurn: sample_rate set to {sample_rate}Hz")
        self._analyzer.set_sample_rate(sample_rate)

    def update_vad_start_secs(self, vad_start_secs: float):
        """Update VAD start seconds."""
        logger.info(f"[Session {self._session_id}] 🧠 SmartTurn: vad_start_secs updated to {vad_start_secs}s")
        self._analyzer.update_vad_start_secs(vad_start_secs)

    def append_audio(self, buffer: bytes, is_speech: bool) -> EndOfTurnState:
        """Append audio data for analysis.

        Args:
            buffer: Raw audio bytes
            is_speech: Whether the audio contains speech (from VAD)

        Returns:
            EndOfTurnState indicating current turn state
        """
        self._audio_chunks_received += 1
        if is_speech:
            self._speech_chunks += 1

        result = self._analyzer.append_audio(buffer, is_speech)

        # Log first chunk to confirm SmartTurn is receiving audio
        if self._audio_chunks_received == 1:
            logger.info(
                f"[Session {self._session_id}] 🧠 SmartTurn: FIRST AUDIO CHUNK RECEIVED - turn analyzer is active!"
            )

        # Log first speech chunk
        if is_speech and self._speech_chunks == 1:
            logger.info(
                f"[Session {self._session_id}] 🧠 SmartTurn: FIRST SPEECH CHUNK - VAD detected speech!"
            )

        # Log on state change (speech_triggered toggled) or every 250 chunks (~8s)
        speech_triggered = self._analyzer.speech_triggered
        state_changed = speech_triggered != self._last_logged_speech_triggered
        if state_changed:
            self._last_logged_speech_triggered = speech_triggered
            logger.info(
                f"[Session {self._session_id}] 🧠 SmartTurn: "
                f"speech_triggered={'START' if speech_triggered else 'STOP'}, "
                f"chunks={self._audio_chunks_received}, speech_chunks={self._speech_chunks}, state={result.name}"
            )
        elif self._audio_chunks_received % 250 == 0:
            logger.info(
                f"[Session {self._session_id}] 🧠 SmartTurn: "
                f"chunks={self._audio_chunks_received}, speech_chunks={self._speech_chunks}, "
                f"speech_triggered={speech_triggered}, state={result.name}"
            )

        return result

    async def analyze_end_of_turn(self) -> Tuple[EndOfTurnState, Optional[MetricsData]]:
        """Analyze if the user has finished speaking.

        This is an async method that delegates to the inner analyzer's
        async analyze_end_of_turn method.

        Returns:
            Tuple of (EndOfTurnState, Optional[MetricsData])
        """
        self._analysis_count += 1

        # Log first analysis to confirm method is being called
        if self._analysis_count == 1:
            logger.info(
                f"[Session {self._session_id}] 🧠 SmartTurn: FIRST ANALYSIS CALL - ML inference starting!"
            )

        # await the async method from the inner analyzer
        state, metrics = await self._analyzer.analyze_end_of_turn()

        # Check if end of turn was detected (COMPLETE = user finished speaking)
        if state == EndOfTurnState.COMPLETE:
            self._end_of_turn_detections += 1
            logger.info(
                f"[Session {self._session_id}] 🧠 SmartTurn: ✅ END-OF-TURN DETECTED "
                f"(analysis #{self._analysis_count}, total detections: {self._end_of_turn_detections})"
            )
        else:
            # Log analysis attempts every 5th call
            if self._analysis_count % 5 == 0:
                logger.info(
                    f"[Session {self._session_id}] 🧠 SmartTurn: analyzing... "
                    f"(#{self._analysis_count}, state={state.name}, speech_triggered={self._analyzer.speech_triggered})"
                )

        return state, metrics

    def clear(self):
        """Clear the analyzer state."""
        logger.info(
            f"[Session {self._session_id}] 🧠 SmartTurn: CLEARED "
            f"(processed {self._audio_chunks_received} chunks, "
            f"{self._speech_chunks} speech chunks, "
            f"{self._analysis_count} analyses, "
            f"{self._end_of_turn_detections} end-of-turn detections)"
        )
        self._analyzer.clear()
        # Reset counters for new utterance
        self._audio_chunks_received = 0
        self._speech_chunks = 0
        self._analysis_count = 0

    async def cleanup(self):
        """Cleanup resources."""
        logger.info(
            f"[Session {self._session_id}] 🧠 SmartTurn: CLEANUP "
            f"(total: {self._audio_chunks_received} chunks, "
            f"{self._speech_chunks} speech chunks, "
            f"{self._analysis_count} analyses, "
            f"{self._end_of_turn_detections} end-of-turn detections)"
        )
        await self._analyzer.cleanup()

    def get_stats(self) -> dict:
        """Get statistics about the analyzer.

        Returns:
            Dictionary with analyzer statistics
        """
        return {
            "session_id": self._session_id,
            "audio_chunks_received": self._audio_chunks_received,
            "speech_chunks": self._speech_chunks,
            "analysis_count": self._analysis_count,
            "end_of_turn_detections": self._end_of_turn_detections,
            "speech_triggered": self._analyzer.speech_triggered,
            "sample_rate": self._analyzer.sample_rate,
        }
