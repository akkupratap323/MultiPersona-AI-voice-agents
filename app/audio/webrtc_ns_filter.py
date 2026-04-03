"""
WebRTC Noise Suppression Filter for Pipecat.

Uses Google's WebRTC audio processing library for real-time noise suppression
and automatic gain control. Works natively with 16kHz audio.

Features:
- Noise suppression (levels 0-4, where 4 is maximum)
- Automatic gain control (levels 0-31 dBFS)
- Voice Activity Detection (VAD)
- Low latency (processes 10ms chunks)
- No API key required (open source)
"""

from loguru import logger

from pipecat.audio.filters.base_audio_filter import BaseAudioFilter
from pipecat.frames.frames import FilterControlFrame, FilterEnableFrame

try:
    from webrtc_noise_gain import AudioProcessor
except ModuleNotFoundError as e:
    logger.error(f"Exception: {e}")
    logger.error(
        "In order to use the WebRTC NS filter, you need to `pip install webrtc-noise-gain`."
    )
    raise Exception(f"Missing module: {e}")


class WebRTCNoiseSuppressionFilter(BaseAudioFilter):
    """Audio filter using WebRTC for noise suppression and auto gain.

    Uses Google's WebRTC audio processing library which is optimized for
    real-time voice communication. Works natively with 16kHz audio.

    Args:
        noise_suppression_level: Noise suppression level (0=disabled, 1-4, 4=max)
        auto_gain_dbfs: Auto gain in dBFS (0=disabled, 1-31)
    """

    def __init__(
        self,
        noise_suppression_level: int = 3,
        auto_gain_dbfs: int = 3,
    ) -> None:
        """Initialize the WebRTC noise suppression filter.

        Args:
            noise_suppression_level: 0 (disabled) to 4 (maximum suppression)
            auto_gain_dbfs: 0 (disabled) to 31 (maximum gain)
        """
        self._filtering = True
        self._sample_rate = 0
        self._noise_level = min(4, max(0, noise_suppression_level))
        self._auto_gain = min(31, max(0, auto_gain_dbfs))
        self._processor = None
        self._buffer = b""

        logger.info(
            f"WebRTC NS Filter initialized: noise_level={self._noise_level}, "
            f"auto_gain={self._auto_gain}dBFS"
        )

    async def start(self, sample_rate: int):
        """Initialize the filter with the transport's sample rate.

        Args:
            sample_rate: The sample rate of the input transport in Hz.
        """
        self._sample_rate = sample_rate

        if sample_rate != 16000:
            logger.warning(
                f"WebRTC NS filter works best with 16kHz audio, but got {sample_rate}Hz. "
                "Audio quality may be affected."
            )

        # Create the audio processor
        self._processor = AudioProcessor(self._auto_gain, self._noise_level)
        logger.info(
            f"WebRTC NS Filter started: sample_rate={sample_rate}Hz, "
            f"noise_suppression={self._noise_level}, auto_gain={self._auto_gain}dBFS"
        )

    async def stop(self):
        """Clean up the filter when stopping."""
        self._processor = None
        self._buffer = b""

    async def process_frame(self, frame: FilterControlFrame):
        """Process control frames to enable/disable filtering.

        Args:
            frame: The control frame containing filter commands.
        """
        if isinstance(frame, FilterEnableFrame):
            self._filtering = frame.enable
            logger.info(f"WebRTC NS Filter {'enabled' if frame.enable else 'disabled'}")

    async def filter(self, audio: bytes) -> bytes:
        """Apply WebRTC noise suppression to audio data.

        Processes audio in 10ms chunks (160 samples at 16kHz = 320 bytes).
        Buffers incoming audio to ensure complete chunks are processed.

        NOTE: When not enough audio has accumulated for a full 10ms chunk,
        this returns empty bytes. This is the same behavior as pipecat's
        built-in Koala filter. The downstream pipeline handles empty frames.

        Args:
            audio: Raw audio data as bytes (16-bit PCM, mono, 16kHz).

        Returns:
            Noise-suppressed audio data as bytes. May return empty bytes
            while buffering (same as Koala filter behavior).
        """
        if not self._filtering or self._processor is None:
            return audio

        # WebRTC requires 10ms chunks (160 samples @ 16kHz = 320 bytes)
        chunk_size = 320  # 10ms at 16kHz, 16-bit mono

        # Add incoming audio to buffer
        self._buffer += audio

        # Process complete 10ms chunks
        output = b""
        while len(self._buffer) >= chunk_size:
            chunk = self._buffer[:chunk_size]
            self._buffer = self._buffer[chunk_size:]

            try:
                result = self._processor.Process10ms(chunk)
                output += result.audio
            except Exception as e:
                logger.error(f"WebRTC NS processing error: {e}")
                output += chunk  # Pass through on error

        return output
