"""Tone-Aware Processor for dynamic voice selection.

This processor sits in the pipeline and detects emotional tone from user speech.
It uses MSP-PODCAST trained wav2vec2 for dimensional emotion detection from voice prosody.

Features:
- MSP-PODCAST model trained on real podcast conversations (not acted speech)
- Dimensional emotions: arousal, dominance, valence (more nuanced)
- Maps dimensions to 4 voice tones (neutral, excited, frustrated, sad)
- Stability system prevents rapid voice switching
- Falls back to text-based detection if unavailable
- Zero cost (fully local inference)
"""

from typing import Optional
import time
import asyncio
import numpy as np

from loguru import logger
from pipecat.frames.frames import (
    Frame,
    TranscriptionFrame,
    InterimTranscriptionFrame,
    TranscriptionUpdateFrame,
    AudioRawFrame,
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.processors.frameworks.rtvi import RTVIServerMessageFrame

from app.services.tone_detector import ToneDetector, TONE_TO_VOICE, DEFAULT_VOICE
from app.services.msp_emotion_detector import (
    get_msp_detector,
    MSPEmotionDetector,
)
from app.services.chatterbox_tts import ChatterboxTTSService
from app.services.hybrid_emotion_detector import HybridEmotionDetector

try:
    from pipecat.services.cartesia.tts import CartesiaTTSService, GenerationConfig
    _CARTESIA_AVAILABLE = True
except ImportError:
    _CARTESIA_AVAILABLE = False


class ToneAwareProcessor(FrameProcessor):
    """Processor that detects emotional tone and switches TTS voice.

    Uses MSP-PODCAST trained wav2vec2 for dimensional emotion detection:
    1. Audio frames are processed by wav2vec2 model (trained on MSP-PODCAST)
    2. Model returns arousal, dominance, valence (0-1 scale)
    3. Dimensions are mapped to our 4 voice tones
    4. Voice is switched based on stability system

    Dimensional emotion mapping:
    - High arousal + negative valence = frustrated
    - High arousal + positive valence = excited
    - Low arousal + negative valence = sad
    - Low/medium arousal + positive valence = neutral

    Flow:
    1. User speaks (frustrated/excited/sad/neutral)
    2. Audio sent to MSP-PODCAST model for dimensional emotion detection
    3. Model returns arousal/dominance/valence
    4. Dimensions mapped to tone (neutral/excited/frustrated/sad)
    5. Stability system checks (cooldown, confidence)
    6. TTS voice switched if stable
    7. Bot responds with appropriate voice

    Attributes:
        emotion_detector: MSPEmotionDetector for audio analysis
        tone_detector: ToneDetector for text-based fallback
        tts_service: Reference to TTS service for voice switching
        enabled: Whether tone-aware voice switching is enabled
        current_voice_model: Currently active voice model
    """

    def __init__(
        self,
        tts_service=None,
        cooldown_seconds: float = 2.0,  # Slightly longer for stability
        enabled: bool = True,
        use_hybrid_mode: bool = True,  # NEW: Enable hybrid audio+text detection
        groq_api_key: str = None,  # LLM API key for text sentiment (supports Google Gemini)
        **kwargs
    ):
        """Initialize the ToneAwareProcessor.

        Args:
            tts_service: Reference to Deepgram TTS service for voice switching
            cooldown_seconds: Minimum time between voice switches
            enabled: Whether to enable tone-aware voice switching
            use_hybrid_mode: Use hybrid audio+text emotion detection (default: True)
            groq_api_key: LLM API key for text sentiment (Google Gemini API key)
            **kwargs: Additional arguments passed to FrameProcessor
        """
        super().__init__(**kwargs)

        # MSP-PODCAST detector (trained on real podcast conversations)
        self.emotion_detector: MSPEmotionDetector = get_msp_detector()

        # Text-based fallback detector
        self.tone_detector = ToneDetector(cooldown_seconds=cooldown_seconds)

        # NEW: Hybrid emotion detector (audio + LLM text sentiment via Google Gemini)
        self.use_hybrid_mode = use_hybrid_mode
        self.hybrid_detector = HybridEmotionDetector(
            audio_detector=self.emotion_detector,
            llm_api_key=groq_api_key  # Now uses Google Gemini API
        ) if use_hybrid_mode else None

        self.tts_service = tts_service
        self.enabled = enabled

        # Voice switching state
        self.current_voice_model: str = DEFAULT_VOICE
        self._current_tone: str = "neutral"

        # Detection state
        self._latest_arousal: float = 0.5
        self._latest_dominance: float = 0.5
        self._latest_valence: float = 0.5
        self._latest_emotion: str = "neutral"
        self._latest_tone: str = "neutral"
        self._latest_confidence: float = 0.0
        self._emotion_timestamp: float = 0.0  # NON-BLOCKING: Track when emotion was last updated
        self._emotion_ttl_seconds: float = 10.0  # NON-BLOCKING: Expire emotions after 10 seconds

        # NEW: Hybrid detection state
        self._latest_transcript: str = ""  # Store last transcript for hybrid mode

        # NON-BLOCKING: Background task tracking
        self._background_tasks: set = set()  # Track running background tasks

        # ===== STABILITY SYSTEM =====
        # Tuned for MSP-PODCAST dimensional emotions:
        # 1. Cooldown: 2.0s (prevent rapid switching)
        # 2. Confidence gate: 25% (dimensional clarity threshold)
        # 3. 2-frame agreement: Require consistent detection

        self._stability_counter: int = 0
        self._stability_last_tone: str = "neutral"
        self._last_switch_time: float = 0.0
        self._switch_cooldown: float = cooldown_seconds
        self._confidence_threshold: float = 0.05  # Dimensional clarity threshold (lowered for more responsive tone adaptation)
        self._stability_frames_required: int = 2   # Require 2 consistent detections

        # Audio buffer for MSP-PODCAST processing
        # 1000ms for better dimensional emotion detection
        self._audio_buffer: bytes = b""
        self._audio_buffer_duration_ms: int = 0
        self._min_buffer_ms: int = 1000  # 1 second for stable dimension detection

        # Voice switch deferral - don't interrupt bot speech
        self._bot_is_speaking: bool = False
        self._pending_voice_switch: Optional[tuple] = None  # (voice, tone) to switch to

        # Deferred emotion detection — run AFTER bot stops speaking to avoid GIL contention
        self._pending_detections: list[tuple] = []  # Queue of (audio_buffer, transcript) from TranscriptionFrames

        # VAD threshold for silence detection
        self._vad_threshold: int = 500  # Skip audio below this amplitude

        # A2UI query capture - forward user queries to VisualHintProcessor
        self._visual_hint_processor = None

        mode_str = "HYBRID (Audio 70% + LLM Text 30%)" if use_hybrid_mode else "AUDIO-ONLY"
        logger.info(
            f"ToneAwareProcessor {mode_str} NON-BLOCKING: MSP-PODCAST, conf=0.25, buffer=1000ms, "
            f"stability=2, cooldown={cooldown_seconds}s, TTL={self._emotion_ttl_seconds}s, ZERO LATENCY"
        )

    async def initialize(self) -> None:
        """Initialize MSP-PODCAST wav2vec2 model (lazy loading)."""
        logger.info(f"[EMOTION-DIAG] ToneAwareProcessor.initialize() called, enabled={self.enabled}")
        if self.enabled:
            logger.info("[EMOTION-DIAG] Calling emotion_detector.connect()...")
            connected = await self.emotion_detector.connect()
            logger.info(
                f"[EMOTION-DIAG] emotion_detector.connect() returned: {connected}, "
                f"is_connected={self.emotion_detector.is_connected}, "
                f"model={self.emotion_detector.model is not None}, "
                f"processor={self.emotion_detector.processor is not None}"
            )
            if connected:
                logger.info("[EMOTION-DIAG] MSP-PODCAST wav2vec2 emotion detection READY")
            else:
                logger.error(
                    "[EMOTION-DIAG] MSP-PODCAST initialization FAILED! "
                    "All audio emotion detection will be disabled. Using text fallback only."
                )
        else:
            logger.info("[EMOTION-DIAG] Emotion detection disabled in config, skipping MSP-PODCAST initialization")

    def set_tts_service(self, tts_service) -> None:
        """Set the TTS service reference for voice switching.

        Args:
            tts_service: The Deepgram TTS service instance
        """
        self.tts_service = tts_service
        logger.info("TTS service connected to ToneAwareProcessor")

    def set_visual_hint_processor(self, visual_hint_processor) -> None:
        """Set the VisualHintProcessor reference for A2UI query capture.

        Args:
            visual_hint_processor: The VisualHintProcessor instance
        """
        self._visual_hint_processor = visual_hint_processor
        logger.info("🎨 VisualHintProcessor connected to ToneAwareProcessor for A2UI query capture")

    def _can_switch_cooldown(self) -> bool:
        """Check if cooldown period has passed since last switch."""
        if self._last_switch_time == 0.0:
            return True
        return (time.time() - self._last_switch_time) >= self._switch_cooldown

    def _is_tone_stable(self, tone: str, confidence: float) -> bool:
        """Check if tone is stable enough for voice switching.

        Args:
            tone: Detected tone
            confidence: Confidence score (dimensional clarity)

        Returns:
            True if stable enough to switch
        """
        # Check confidence gate (dimensional clarity)
        if confidence < self._confidence_threshold:
            self._stability_counter = 0
            return False

        # Check cooldown
        if not self._can_switch_cooldown():
            return False

        # Track consecutive same-tone detections
        if tone == self._stability_last_tone:
            self._stability_counter += 1
        else:
            self._stability_last_tone = tone
            self._stability_counter = 1

        is_stable = self._stability_counter >= self._stability_frames_required

        if is_stable:
            logger.info(
                f"STABLE (MSP): {tone} ({confidence:.0%}) "
                f"[{self._stability_counter}/{self._stability_frames_required}]"
            )

        return is_stable

    def _record_switch(self, tone: str) -> None:
        """Record that a voice switch happened."""
        self._last_switch_time = time.time()
        self._stability_counter = 0
        self._current_tone = tone

    def _get_current_tone(self) -> str:
        """Get the current tone (with freshness check)."""
        # Check if emotion has expired
        if self._emotion_timestamp > 0:
            age = time.time() - self._emotion_timestamp
            if age > self._emotion_ttl_seconds:
                # Emotion expired, reset to neutral
                if self._current_tone != "neutral":
                    logger.info(f"⏰ Emotion expired ({age:.1f}s > {self._emotion_ttl_seconds}s), reset to neutral")
                    self._current_tone = "neutral"
                    self._latest_tone = "neutral"
                    self._latest_emotion = "neutral"
        return self._current_tone

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process frames for emotion detection and voice switching.

        Args:
            frame: The frame to process
            direction: Direction of frame flow
        """
        await super().process_frame(frame, direction)

        if not self.enabled:
            await self.push_frame(frame, direction)
            return

        # Periodic frame type logging (every 500 audio frames)
        if isinstance(frame, AudioRawFrame):
            if not hasattr(self, '_frame_count'):
                self._frame_count = 0
            self._frame_count += 1
            if self._frame_count % 500 == 1:
                logger.debug(
                    f"[EMOTION-DIAG] AudioRawFrame #{self._frame_count}: "
                    f"direction={direction}, audio_len={len(frame.audio)}, "
                    f"sample_rate={getattr(frame, 'sample_rate', 'N/A')}, "
                    f"detector_connected={self.emotion_detector.is_connected}"
                )

        # Track bot speaking state to avoid interrupting speech
        if isinstance(frame, BotStartedSpeakingFrame):
            self._bot_is_speaking = True
            # Clear stale audio buffer — no point detecting emotion on leftover mic audio
            self._audio_buffer = b""
            self._audio_buffer_duration_ms = 0
            # NOTE: Do NOT cancel background MSP tasks here. Voice switching is already
            # guarded by _bot_is_speaking in _switch_voice_now(), which defers any voice
            # change until bot finishes speaking. Cancelling the task would prevent the
            # hybrid emotion event from being emitted to the frontend entirely.
            logger.debug("Bot started speaking - voice switches deferred")

        elif isinstance(frame, BotStoppedSpeakingFrame):
            self._bot_is_speaking = False
            logger.debug("Bot stopped speaking")
            # Apply any pending voice switch now that bot finished speaking
            if self._pending_voice_switch:
                voice, tone = self._pending_voice_switch
                self._pending_voice_switch = None
                await self._apply_voice_switch(voice, tone)

        # Buffer audio frames for MSP-PODCAST (only during user speech, not bot speech or silence)
        if isinstance(frame, AudioRawFrame) and direction == FrameDirection.DOWNSTREAM:
            if not self._bot_is_speaking and self.emotion_detector.is_connected:
                self._buffer_audio_frame(frame)

        # Process transcription frames for fallback/logging
        transcription_types = (
            TranscriptionFrame,
            InterimTranscriptionFrame,
            TranscriptionUpdateFrame,
        )
        if isinstance(frame, transcription_types):
            text = getattr(frame, "text", "")
            is_final = isinstance(frame, TranscriptionFrame)

            # Only log final transcriptions at INFO; interim at DEBUG
            if is_final:
                logger.info(f"📥 TranscriptionFrame: '{text}'")
            else:
                logger.debug(f"📥 {type(frame).__name__}: '{text}'")

            # Store transcript for hybrid mode
            if text and text.strip():
                self._latest_transcript = text
                if is_final:
                    logger.info(f"💾 Stored transcript for hybrid: '{text[:50]}'...")

                # Forward to VisualHintProcessor for A2UI query capture
                if self._visual_hint_processor is not None:
                    self._visual_hint_processor.set_current_query(text)

            # On final transcription: run emotion detection immediately in background
            # Voice switching is deferred by _switch_voice_now() if bot is speaking,
            # but detection runs now so result is ready when bot stops
            if isinstance(frame, TranscriptionFrame) and text and text.strip():
                if self.emotion_detector.is_connected and len(self._audio_buffer) > 0:
                    buffer_copy = self._audio_buffer
                    self._audio_buffer = b""
                    self._audio_buffer_duration_ms = 0
                    # Run detection immediately (non-blocking background task)
                    await self._trigger_emotion_detection(buffer_copy, text)
                    logger.debug(
                        f"[EMOTION-DIAG] Triggered immediate detection: "
                        f"buffer={len(buffer_copy)/32:.0f}ms, "
                        f"transcript='{text[:30]}...'"
                    )
                elif not self.emotion_detector.is_connected:
                    await self._process_text_fallback(text)

        # Always pass frame downstream
        await self.push_frame(frame, direction)

    def _buffer_audio_frame(self, frame: AudioRawFrame) -> None:
        """Buffer audio frame for later emotion detection (lightweight, no CPU work).

        Only buffers non-silent frames. Detection is triggered separately when
        a final TranscriptionFrame arrives, not on buffer duration.

        Args:
            frame: Audio frame with raw PCM data
        """
        # Quick amplitude check to skip silence (avoid numpy for speed)
        audio_array = np.frombuffer(frame.audio, dtype=np.int16)
        mean_amplitude = np.mean(np.abs(audio_array))
        if mean_amplitude < self._vad_threshold:
            return  # Skip silent frames

        # Add to buffer, cap at 3 seconds (96000 bytes at 16kHz 16-bit) to prevent unbounded growth
        self._audio_buffer += frame.audio
        max_buffer_bytes = 96000  # 3 seconds at 16kHz * 2 bytes
        if len(self._audio_buffer) > max_buffer_bytes:
            # Keep only the last 2 seconds (most relevant for emotion)
            self._audio_buffer = self._audio_buffer[-64000:]

    async def _trigger_emotion_detection(self, audio_buffer: bytes, transcript: str) -> None:
        """Trigger emotion detection in background.

        Called after bot stops speaking to avoid GIL contention with audio output.

        Args:
            audio_buffer: Saved audio data from user speech
            transcript: The final transcription text
        """
        buffer_duration_ms = len(audio_buffer) / 32  # 16kHz * 2 bytes = 32 bytes/ms

        logger.debug(
            f"[EMOTION-DIAG] Deferred detection: "
            f"buffer={buffer_duration_ms:.0f}ms, transcript='{transcript[:30]}...'"
        )

        # Get sample rate (default 16kHz)
        sample_rate = 16000

        # Create background task for emotion detection
        task = asyncio.create_task(
            self._detect_emotion_async(audio_buffer, sample_rate, transcript)
        )
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def _detect_emotion_async(
        self,
        audio_buffer: bytes,
        sample_rate: int,
        transcript: str
    ) -> None:
        """Background task for emotion detection (NON-BLOCKING).

        This runs in parallel with the pipeline and updates emotion state
        when ready. The pipeline never waits for this to complete.

        Args:
            audio_buffer: Audio data to process
            sample_rate: Sample rate of audio
            transcript: Transcript for hybrid mode
        """
        try:
            logger.debug(
                f"[EMOTION-DIAG] _detect_emotion_async: "
                f"buffer={len(audio_buffer)}B, sr={sample_rate}, "
                f"hybrid={self.use_hybrid_mode}, connected={self.emotion_detector.is_connected}"
            )

            # ===== HYBRID MODE: Audio + Text =====
            if self.use_hybrid_mode and self.hybrid_detector:

                # Get audio emotion first
                audio_result = await self.emotion_detector.process_audio(
                    audio_buffer,
                    sample_rate=sample_rate
                )

                if audio_result is None:
                    logger.warning(
                        f"[EMOTION-DIAG] process_audio returned None! "
                        f"enabled={self.emotion_detector.enabled}, "
                        f"is_connected={self.emotion_detector.is_connected}, "
                        f"model={self.emotion_detector.model is not None}, "
                        f"buffer_len={len(audio_buffer)}, "
                        f"min_bytes_needed={int(sample_rate * 2 * 0.5)}"
                    )
                    return

                if audio_result:
                    # Convert to dict format for hybrid detector
                    audio_dict = {
                        "emotion": audio_result.emotion,
                        "arousal": audio_result.arousal,
                        "valence": audio_result.valence,
                        "dominance": audio_result.dominance,
                        "confidence": audio_result.confidence
                    }

                    # Fuse with text sentiment
                    hybrid_result = await self.hybrid_detector.detect_hybrid_emotion(
                        audio_emotion_result=audio_dict,
                        transcript=transcript
                    )

                    # Log detailed hybrid results
                    logger.info(
                        f"🎯 [BG] HYBRID RESULT:\n"
                        f"  Primary Emotion: {hybrid_result['primary_emotion']} "
                        f"(confidence: {hybrid_result['overall_confidence']:.0%})\n"
                        f"  Audio: {audio_dict['emotion']} ({audio_dict['confidence']:.0%}) "
                        f"× {hybrid_result['weights']['audio']:.0%}\n"
                        f"  Text:  {hybrid_result['components']['text']['emotion']} "
                        f"({hybrid_result['components']['text']['confidence']:.0%}) "
                        f"× {hybrid_result['weights']['text']:.0%}\n"
                        f"  Mismatch: {hybrid_result['mismatch_detected']} "
                        f"{hybrid_result.get('interpretation', '')}\n"
                        f"  Fused A/V/D: {hybrid_result['arousal']:.2f}/"
                        f"{hybrid_result['valence']:.2f}/{hybrid_result['dominance']:.2f}\n"
                        f"  Tokens Used: {hybrid_result['tokens_used']}"
                    )

                    # Update state with hybrid results (thread-safe for asyncio)
                    self._latest_arousal = hybrid_result['arousal']
                    self._latest_dominance = hybrid_result['dominance']
                    self._latest_valence = hybrid_result['valence']
                    self._latest_emotion = hybrid_result['primary_emotion']
                    self._latest_tone = hybrid_result['primary_emotion']
                    self._latest_confidence = hybrid_result['overall_confidence']
                    self._emotion_timestamp = time.time()  # Track freshness

                    # Pass emotion directly to voice switching (matches Chatterbox EMOTION_TO_PARAMS)
                    detected_tone = hybrid_result['primary_emotion']

                    # Emit hybrid emotion to frontend
                    await self._emit_hybrid_emotion_event(hybrid_result)

                    # Check voice switch with hybrid confidence
                    if hybrid_result['overall_confidence'] >= self._confidence_threshold:
                        await self._check_voice_switch(
                            detected_tone,
                            hybrid_result['overall_confidence']
                        )

            # ===== AUDIO-ONLY MODE (Original) =====
            else:
                logger.info("[EMOTION-DIAG] AUDIO-ONLY MODE: Processing audio emotion")

                # Send to MSP-PODCAST for dimensional emotion detection
                result = await self.emotion_detector.process_audio(
                    audio_buffer,
                    sample_rate=sample_rate
                )

                if result is None:
                    logger.warning(
                        f"[EMOTION-DIAG] AUDIO-ONLY: process_audio returned None! "
                        f"enabled={self.emotion_detector.enabled}, "
                        f"is_connected={self.emotion_detector.is_connected}, "
                        f"model={self.emotion_detector.model is not None}, "
                        f"buffer_len={len(audio_buffer)}"
                    )

                if result:
                    self._latest_arousal = result.arousal
                    self._latest_dominance = result.dominance
                    self._latest_valence = result.valence
                    self._latest_emotion = result.emotion
                    self._latest_tone = result.tone
                    self._latest_confidence = result.confidence
                    self._emotion_timestamp = time.time()  # Track freshness

                    logger.info(
                        f"🎤 [BG] AUDIO-ONLY RESULT: {result.emotion} "
                        f"(confidence: {result.confidence:.0%}, "
                        f"A={result.arousal:.2f}, V={result.valence:.2f})"
                    )

                    # Emit emotion data to frontend via WebSocket
                    await self._emit_emotion_event(result)

                    # Check if we should switch voice (only if above threshold)
                    if result.confidence >= self._confidence_threshold:
                        await self._check_voice_switch(result.tone, result.confidence)

        except Exception as e:
            logger.error(f"[BG] Emotion processing error: {e}")
            import traceback
            traceback.print_exc()

    async def _process_text_fallback(self, text: str) -> None:
        """Process text with LLM-based tone detection (fallback).

        Used when MSP-PODCAST is not available.

        Args:
            text: Transcribed text
        """
        try:
            tone = await self.tone_detector.detect_tone_llm(text)
            confidence = 0.7  # Text-based detection has moderate confidence

            # Map tone to VAD (arousal, dominance, valence) values
            # These are reasonable approximations for text-based detection
            tone_to_vad = {
                "neutral": {"arousal": 0.5, "dominance": 0.5, "valence": 0.5},
                "excited": {"arousal": 0.8, "dominance": 0.6, "valence": 0.8},
                "frustrated": {"arousal": 0.7, "dominance": 0.4, "valence": 0.3},
                "sad": {"arousal": 0.3, "dominance": 0.3, "valence": 0.3},
                "happy": {"arousal": 0.7, "dominance": 0.6, "valence": 0.8},
                "angry": {"arousal": 0.8, "dominance": 0.7, "valence": 0.2},
            }

            vad = tone_to_vad.get(tone, tone_to_vad["neutral"])

            # Update state variables
            self._latest_arousal = vad["arousal"]
            self._latest_dominance = vad["dominance"]
            self._latest_valence = vad["valence"]
            self._latest_emotion = tone
            self._latest_tone = tone
            self._latest_confidence = confidence

            logger.info(f"TEXT FALLBACK: {tone} ({confidence:.0%}) - A:{vad['arousal']:.2f} D:{vad['dominance']:.2f} V:{vad['valence']:.2f}")

            # Emit emotion event to frontend via WebSocket
            await self._emit_text_emotion_event(tone, vad, confidence)

            await self._check_voice_switch(tone, confidence)

        except Exception as e:
            logger.error(f"Text tone detection error: {e}")
            import traceback
            traceback.print_exc()

    async def _check_voice_switch(self, tone: str, confidence: float) -> None:
        """Check if voice should be switched based on detected tone.

        Args:
            tone: Detected tone
            confidence: Confidence score
        """
        current_tone = self._get_current_tone()

        logger.debug(
            f"_check_voice_switch: tone={tone}, current={current_tone}, "
            f"tts_service={self.tts_service is not None}"
        )

        # Only switch if tone is different
        if tone != current_tone:
            is_stable = self._is_tone_stable(tone, confidence)
            has_tts = self.tts_service is not None

            logger.info(
                f"VOICE SWITCH CHECK: tone={tone}, stable={is_stable}, "
                f"tts_connected={has_tts}, current={current_tone}"
            )

            if is_stable and has_tts:
                voice = TONE_TO_VOICE.get(tone, DEFAULT_VOICE)
                self._record_switch(tone)
                logger.info(f"INITIATING VOICE SWITCH: {current_tone} -> {tone} (voice: {voice})")
                await self._switch_voice_now(voice, tone)
            else:
                logger.debug(
                    f"Tone: {tone} ({confidence:.0%}) - "
                    f"waiting [{self._stability_counter}/{self._stability_frames_required}]"
                )

    async def _switch_voice_now(self, new_voice: str, tone: str) -> None:
        """Request voice switch - defers if bot is speaking.

        Args:
            new_voice: The new voice model to use
            tone: The detected emotional tone
        """
        logger.info(
            f"_switch_voice_now called: new_voice={new_voice}, tone={tone}, "
            f"tts_service={self.tts_service is not None}, bot_speaking={self._bot_is_speaking}"
        )

        if not self.tts_service:
            logger.warning("Cannot switch voice: TTS service not connected")
            return

        # If bot is currently speaking, defer the switch until it finishes
        if self._bot_is_speaking:
            self._pending_voice_switch = (new_voice, tone)
            logger.info(
                f"VOICE SWITCH DEFERRED: {self.current_voice_model} -> {new_voice} "
                f"(tone: {tone}) - waiting for bot to finish speaking"
            )
            return

        # Bot not speaking, apply immediately
        logger.info(f"Bot not speaking, applying voice switch immediately")
        await self._apply_voice_switch(new_voice, tone)

    async def _apply_voice_switch(self, new_voice: str, tone: str) -> None:
        """Actually apply the voice switch (only call when bot is not speaking).

        For Chatterbox TTS: Uses set_emotion() to control exaggeration and cfg_weight
        For other TTS: Uses set_voice() to switch voice model

        Args:
            new_voice: The new voice model to use (for non-Chatterbox TTS)
            tone: The detected emotional tone
        """
        logger.info(
            f"_apply_voice_switch called: new_voice={new_voice}, tone={tone}, "
            f"tts_service type={type(self.tts_service).__name__}"
        )

        if not self.tts_service:
            logger.warning("_apply_voice_switch: No TTS service!")
            return

        try:
            old_tone = self._current_tone

            # Check if using Chatterbox TTS (emotion-based control via exaggeration/cfg_weight)
            if isinstance(self.tts_service, ChatterboxTTSService):
                logger.info(f"Chatterbox TTS: Setting emotion to '{tone}'")
                self.tts_service.set_emotion(tone)
                self.current_voice_model = tone
                logger.info(f"✅ EMOTION SWITCHED (Chatterbox): {old_tone} -> {tone}")
                await self._emit_tone_switch_event(old_tone, tone)

            # Cartesia TTS — emotion + speed + volume via generation_config in _settings
            elif _CARTESIA_AVAILABLE and isinstance(self.tts_service, CartesiaTTSService):
                # Map our internal emotion names to Cartesia emotion strings + speed/volume tuning.
                # Speed: 0.6 (slowest) → 1.5 (fastest). Volume: 0.5 (quietest) → 2.0 (loudest).
                # Primary emotions (best results): neutral, angry, excited, content, sad, scared
                # Extended: enthusiastic, melancholic, frustrated, agitated, calm, anxious, etc.
                CARTESIA_EMOTION_CONFIG = {
                    # user emotion  → (cartesia_emotion,  speed,  volume)
                    "neutral":       ("neutral",           1.0,    1.0),
                    "happy":         ("happy",             1.1,    1.1),
                    "excited":       ("enthusiastic",      1.2,    1.2),   # more energy than plain "excited"
                    "frustrated":    ("agitated",          1.05,   1.1),   # slightly faster, louder = tense
                    "angry":         ("angry",             1.1,    1.3),   # loud and direct
                    "sad":           ("melancholic",       0.85,   0.9),   # slower, quieter = heavy-hearted
                    "fear":          ("scared",            0.95,   0.85),  # quieter, slightly slower
                    "content":       ("content",           0.95,   0.95),  # calm and settled
                    "empathetic":    ("sympathetic",       0.9,    0.95),  # warm and measured
                    "anxious":       ("anxious",           1.1,    0.9),   # faster but softer
                    "curious":       ("curious",           1.0,    1.0),
                    "confident":     ("confident",         1.05,   1.1),
                    "disappointed":  ("disappointed",      0.9,    0.9),
                    "apologetic":    ("apologetic",        0.9,    0.9),
                    "determined":    ("determined",        1.05,   1.1),
                    "sarcastic":     ("sarcastic",         1.0,    1.0),
                    "joking":        ("joking/comedic",    1.05,   1.05),
                }
                cartesia_emotion, speed, volume = CARTESIA_EMOTION_CONFIG.get(
                    tone, ("neutral", 1.0, 1.0)
                )
                logger.info(
                    f"Cartesia TTS: emotion='{cartesia_emotion}' speed={speed} volume={volume} "
                    f"(from internal tone='{tone}')"
                )
                self.tts_service._settings["generation_config"] = GenerationConfig(
                    emotion=cartesia_emotion,
                    speed=speed,
                    volume=volume,
                )
                self.current_voice_model = tone
                logger.info(
                    f"✅ EMOTION SWITCHED (Cartesia): {old_tone} -> {tone} "
                    f"(cartesia='{cartesia_emotion}', speed={speed}, volume={volume})"
                )
                await self._emit_tone_switch_event(old_tone, tone)

            else:
                # Other TTS providers: Use voice ID switching
                old_voice = self.current_voice_model
                logger.info(f"Calling tts_service.set_voice('{new_voice}')")
                self.tts_service.set_voice(new_voice)
                self.current_voice_model = new_voice
                actual_voice = getattr(self.tts_service, '_voice_id', 'unknown')
                logger.info(f"TTS service _voice_id is now: {actual_voice}")
                logger.info(f"✅ VOICE SWITCHED: {old_voice} -> {new_voice} (tone: {tone})")
                await self._emit_tone_switch_event(old_voice, new_voice)

        except Exception as e:
            logger.error(f"Error switching voice/emotion: {e}")
            import traceback
            traceback.print_exc()

    async def _emit_hybrid_emotion_event(self, hybrid_result: dict) -> None:
        """Emit hybrid emotion detection event to frontend via WebSocket.

        Args:
            hybrid_result: Hybrid emotion result dictionary
        """
        try:
            # Create hybrid emotion data payload for frontend
            emotion_data = {
                "message_type": "hybrid_emotion_detected",
                "primary_emotion": hybrid_result['primary_emotion'],
                "secondary_emotion": hybrid_result.get('secondary_emotion'),
                "arousal": round(hybrid_result['arousal'], 2),
                "valence": round(hybrid_result['valence'], 2),
                "dominance": round(hybrid_result['dominance'], 2),
                "confidence": round(hybrid_result['overall_confidence'], 2),
                "audio_emotion": hybrid_result['components']['audio']['emotion'],
                "text_emotion": hybrid_result['components']['text']['emotion'],
                "audio_weight": round(hybrid_result['weights']['audio'], 2),
                "text_weight": round(hybrid_result['weights']['text'], 2),
                "mismatch_detected": hybrid_result['mismatch_detected'],
                "interpretation": hybrid_result.get('interpretation', ''),
                "tokens_used": hybrid_result['tokens_used'],
                "timestamp": time.time(),
            }

            data_frame = RTVIServerMessageFrame(data=emotion_data)
            await self.push_frame(data_frame)

            logger.info(
                f"✓ Emitted hybrid emotion event: {hybrid_result['primary_emotion']} "
                f"({hybrid_result['overall_confidence']:.0%})"
            )

        except Exception as e:
            logger.error(f"Error emitting hybrid emotion event: {e}")

    async def _emit_emotion_event(self, result) -> None:
        """Emit emotion detection event to frontend via WebSocket.

        Args:
            result: MSPEmotionResult with arousal, dominance, valence, emotion, tone, confidence
        """
        try:
            # Create emotion data payload for frontend
            # Use RTVI-compliant "server-message" type for proper callback routing
            emotion_data = {
                "message_type": "emotion_detected",
                "arousal": round(result.arousal, 2),
                "dominance": round(result.dominance, 2),
                "valence": round(result.valence, 2),
                "emotion": result.emotion,
                "tone": result.tone,
                "confidence": round(result.confidence, 2),
                "timestamp": result.timestamp,
            }

            data_frame = RTVIServerMessageFrame(data=emotion_data)
            await self.push_frame(data_frame)

            logger.info(f"✓ Emitted emotion event via WebSocket: {result.emotion} ({result.confidence:.0%}) - A:{result.arousal:.2f} D:{result.dominance:.2f} V:{result.valence:.2f}")

        except Exception as e:
            logger.error(f"Error emitting emotion event: {e}")

    async def _emit_text_emotion_event(self, tone: str, vad: dict, confidence: float) -> None:
        """Emit text-based emotion detection event to frontend via WebSocket.

        Used when MSP-PODCAST is unavailable and we fall back to text-based detection.

        Args:
            tone: Detected emotional tone
            vad: Dictionary with arousal, dominance, valence values
            confidence: Confidence score
        """
        try:
            # Create emotion data payload for frontend (text fallback)
            emotion_data = {
                "message_type": "emotion_detected",
                "arousal": round(vad["arousal"], 2),
                "dominance": round(vad["dominance"], 2),
                "valence": round(vad["valence"], 2),
                "emotion": tone,
                "tone": tone,
                "confidence": round(confidence, 2),
                "timestamp": time.time(),
                "source": "text_fallback",
            }

            data_frame = RTVIServerMessageFrame(data=emotion_data)
            await self.push_frame(data_frame)

            logger.info(f"✓ Emitted text emotion event via WebSocket: {tone} ({confidence:.0%}) - A:{vad['arousal']:.2f} D:{vad['dominance']:.2f} V:{vad['valence']:.2f}")

        except Exception as e:
            logger.error(f"Error emitting text emotion event: {e}")

    async def _emit_tone_switch_event(self, old_tone: str, new_tone: str) -> None:
        """Emit tone switch event to frontend via WebSocket.

        Args:
            old_tone: Previous tone/voice
            new_tone: New tone/voice
        """
        try:
            # Create tone switch payload for frontend
            # Use RTVI-compliant "server-message" type for proper callback routing
            switch_data = {
                "message_type": "tone_switched",
                "old_tone": old_tone,
                "new_tone": new_tone,
                "timestamp": time.time(),
            }

            data_frame = RTVIServerMessageFrame(data=switch_data)
            await self.push_frame(data_frame)

            logger.debug(f"Emitted tone switch event: {old_tone} -> {new_tone}")

        except Exception as e:
            logger.error(f"Error emitting tone switch event: {e}")

    def get_current_voice(self) -> str:
        """Get the current TTS voice."""
        return self.current_voice_model

    def get_stats(self) -> dict:
        """Get processor statistics."""
        return {
            "enabled": self.enabled,
            "msp_connected": self.emotion_detector.is_connected,
            "tts_connected": self.tts_service is not None,
            "current_voice_model": self.current_voice_model,
            "current_tone": self._current_tone,
            "latest_arousal": self._latest_arousal,
            "latest_dominance": self._latest_dominance,
            "latest_valence": self._latest_valence,
            "latest_emotion": self._latest_emotion,
            "latest_tone": self._latest_tone,
            "latest_confidence": self._latest_confidence,
            "stability_counter": self._stability_counter,
            "stability_last_tone": self._stability_last_tone,
            "stability_frames_required": self._stability_frames_required,
            "switch_cooldown": self._switch_cooldown,
            "confidence_threshold": self._confidence_threshold,
            "time_since_last_switch": (
                time.time() - self._last_switch_time
                if self._last_switch_time > 0
                else None
            ),
        }

    def reset(self) -> None:
        """Reset detector and voice state to default."""
        self.tone_detector.reset()
        self.emotion_detector.reset()
        self.current_voice_model = DEFAULT_VOICE
        self._current_tone = "neutral"
        self._latest_arousal = 0.5
        self._latest_dominance = 0.5
        self._latest_valence = 0.5
        self._latest_emotion = "neutral"
        self._latest_tone = "neutral"
        self._latest_confidence = 0.0
        self._stability_counter = 0
        self._stability_last_tone = "neutral"
        self._last_switch_time = 0.0
        self._audio_buffer = b""
        self._audio_buffer_duration_ms = 0
        self._bot_is_speaking = False
        self._pending_voice_switch = None
        self._pending_detections.clear()

        if self.tts_service:
            if isinstance(self.tts_service, ChatterboxTTSService):
                self.tts_service.set_emotion("neutral")
                logger.info("Emotion reset to neutral (Chatterbox)")
            else:
                self.tts_service.set_voice(DEFAULT_VOICE)
                logger.info(f"Voice reset to default: {DEFAULT_VOICE}")

    async def cleanup(self) -> None:
        """Clean up resources and cancel background tasks."""
        # Cancel any running background emotion detection tasks
        if self._background_tasks:
            logger.info(f"Cancelling {len(self._background_tasks)} background emotion tasks...")
            for task in self._background_tasks:
                if not task.done():
                    task.cancel()
            # Wait for all tasks to complete cancellation
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
            self._background_tasks.clear()

        await self.emotion_detector.disconnect()
        logger.info("ToneAwareProcessor cleaned up")
