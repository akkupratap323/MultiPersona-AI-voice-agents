"""
Subtitle Sync Processor - Emits streaming_text subtitles from TTS word frames.

In pipecat 0.0.98, TTS pushes TTSTextFrame DOWNSTREAM with PTS timestamps
before audio reaches the transport. Words arrive as a burst before audio plays.

This processor emits each word immediately with its pts_offset (seconds from
first word). The frontend buffers words and schedules display relative to
BotStartedSpeaking for audio-synced subtitles.

Pipeline position: between TTS and transport.output()
"""

import time
import uuid

from loguru import logger
from pipecat.frames.frames import Frame, TTSTextFrame, TTSStartedFrame, TTSStoppedFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.processors.frameworks.rtvi import RTVIServerMessageFrame
from pipecat.utils.time import nanoseconds_to_seconds


class SubtitleSyncProcessor(FrameProcessor):
    """Intercepts downstream TTSTextFrame and emits streaming_text
    messages with PTS timing for frontend-side audio sync."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._utterance_id: str | None = None
        self._sequence_counter: int = 0
        self._base_pts: float | None = None  # PTS of first word (seconds)

        logger.info("[SUBTITLE-SYNC] SubtitleSyncProcessor initialized")

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        try:
            if direction == FrameDirection.DOWNSTREAM:
                if isinstance(frame, TTSStartedFrame):
                    self._utterance_id = str(uuid.uuid4())
                    self._sequence_counter = 0
                    self._base_pts = None
                    logger.info(
                        f"[SUBTITLE-SYNC] TTSStartedFrame -> new utterance: {self._utterance_id[:8]}"
                    )

                elif isinstance(frame, TTSTextFrame):
                    word = frame.text if hasattr(frame, "text") else ""
                    if word and word.strip() and self._utterance_id:
                        self._sequence_counter += 1
                        word_pts_secs = nanoseconds_to_seconds(frame.pts) if frame.pts else 0.0

                        if self._base_pts is None:
                            self._base_pts = word_pts_secs

                        pts_offset = word_pts_secs - self._base_pts

                        await self._emit_word(
                            word.strip(),
                            self._sequence_counter,
                            self._utterance_id,
                            pts_offset,
                        )

                elif isinstance(frame, TTSStoppedFrame):
                    if self._utterance_id:
                        logger.info(
                            f"[SUBTITLE-SYNC] TTSStoppedFrame -> finalizing "
                            f"{self._utterance_id[:8]} ({self._sequence_counter} words)"
                        )
                        await self._emit_final(self._sequence_counter + 1, self._utterance_id)
                        self._utterance_id = None
                        self._sequence_counter = 0
                        self._base_pts = None
        except Exception as e:
            logger.error(f"[SUBTITLE-SYNC] Error in process_frame: {e}", exc_info=True)

        # Always pass frames through — even if subtitle emission fails
        await self.push_frame(frame, direction)

    async def _emit_word(self, word: str, seq: int, utterance_id: str, pts_offset: float) -> None:
        """Emit a single word as a streaming_text event with PTS offset."""
        message_data = {
            "message_type": "streaming_text",
            "text": word,
            "is_final": False,
            "sequence_id": seq,
            "utterance_id": utterance_id,
            "pts_offset": round(pts_offset, 4),
            "timestamp": time.time(),
        }
        try:
            data_frame = RTVIServerMessageFrame(data=message_data)
            await self.push_frame(data_frame)
            logger.debug(
                f"[SUBTITLE-SYNC] word='{word}' seq={seq} pts={pts_offset:.3f}s utterance={utterance_id[:8]}"
            )
        except Exception as e:
            logger.error(f"[SUBTITLE-SYNC] Failed to emit word: {e}")

    async def _emit_final(self, seq: int, utterance_id: str) -> None:
        """Emit is_final=True marker to signal end of subtitle stream."""
        message_data = {
            "message_type": "streaming_text",
            "text": "",
            "is_final": True,
            "sequence_id": seq,
            "utterance_id": utterance_id,
            "pts_offset": -1,
            "timestamp": time.time(),
        }
        try:
            data_frame = RTVIServerMessageFrame(data=message_data)
            await self.push_frame(data_frame)
            logger.info(
                f"[SUBTITLE-SYNC] Finalized utterance {utterance_id[:8]}"
            )
        except Exception as e:
            logger.error(f"[SUBTITLE-SYNC] Failed to emit final marker: {e}")
