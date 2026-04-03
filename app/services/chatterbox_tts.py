"""
Chatterbox TTS Service using Resemble AI Cloud API.

This module provides text-to-speech functionality using Resemble AI's
Chatterbox model with emotion control via exaggeration and cfg_weight parameters.

Compatible with Pipecat pipeline framework.
"""

import time
import aiohttp
from typing import Optional, Dict, Any, AsyncGenerator

from loguru import logger
from pipecat.frames.frames import (
    Frame,
    TTSAudioRawFrame,
    TTSStartedFrame,
    TTSStoppedFrame,
    ErrorFrame,
)
from pipecat.processors.frameworks.rtvi import RTVIServerMessageFrame
from pipecat.services.tts_service import TTSService


# Emotion to Chatterbox parameter mapping
# Exaggeration: 0.25-2.0 (higher = more emotional)
# CFG Weight: 0.0-1.0 (lower = faster, more expressive)
EMOTION_TO_PARAMS = {
    "neutral": {"exaggeration": 0.5, "cfg_weight": 0.3},     # Natural pace, slightly expressive
    "sad": {"exaggeration": 0.8, "cfg_weight": 0.3},         # Softer, slower, empathetic
    "frustrated": {"exaggeration": 0.7, "cfg_weight": 0.35}, # Firm, slightly tense
    "excited": {"exaggeration": 1.2, "cfg_weight": 0.2},     # High energy, fast, expressive
    "happy": {"exaggeration": 1.0, "cfg_weight": 0.25},      # Warm, upbeat, bright
    "angry": {"exaggeration": 0.9, "cfg_weight": 0.3},       # Controlled intensity
    "fear": {"exaggeration": 0.6, "cfg_weight": 0.4},        # Gentle, calming
    "content": {"exaggeration": 0.35, "cfg_weight": 0.55},   # Relaxed, near neutral
}

# Voice name to emotion mapping (for compatibility with existing voice switching)
VOICE_TO_EMOTION = {
    "aura-2-athena-en": "neutral",
    "aura-2-vesta-en": "sad",
    "aura-2-neptune-en": "frustrated",
    "aura-2-thalia-en": "excited",
    "aura-2-luna-en": "fear",
    "neutral": "neutral",
    "sad": "sad",
    "frustrated": "frustrated",
    "excited": "excited",
    "happy": "happy",
    "angry": "angry",
}

DEFAULT_PARAMS = {"exaggeration": 0.5, "cfg_weight": 0.5}


class ChatterboxTTSService(TTSService):
    """Pipecat-compatible Chatterbox TTS service using Resemble AI Cloud API.

    This service provides emotion-aware text-to-speech using Chatterbox's
    exaggeration and cfg_weight parameters to control emotional expression.
    """

    def __init__(
        self,
        *,
        api_key: str,
        voice_uuid: str,
        synthesis_url: str = "https://f.cluster.resemble.ai/synthesize",
        stream_url: str = "https://f.cluster.resemble.ai/stream",
        sample_rate: int = 24000,
        model: str = "chatterbox-turbo",
        voice: str = "neutral",
        **kwargs,
    ):
        """Initialize the Chatterbox TTS service.

        Args:
            api_key: Resemble AI API key
            voice_uuid: Resemble AI voice UUID (required for API authentication)
            synthesis_url: URL for synthesis endpoint
            stream_url: URL for streaming endpoint
            sample_rate: Audio sample rate (default 24000)
            model: Resemble model to use (default "chatterbox-turbo" for lower latency)
            voice: Initial voice/emotion (default "neutral")
            **kwargs: Additional arguments for parent class
        """
        super().__init__(sample_rate=sample_rate, push_text_frames=False, **kwargs)

        self._api_key = api_key
        self._voice_uuid = voice_uuid
        self._synthesis_url = synthesis_url
        self._stream_url = stream_url
        self._sample_rate = sample_rate
        self._model = model
        self._voice_id = voice
        self._current_emotion = VOICE_TO_EMOTION.get(voice, "neutral")
        self._session: Optional[aiohttp.ClientSession] = None

        logger.info(
            f"ChatterboxTTSService initialized "
            f"(model: {model}, synthesis: {synthesis_url}, voice_uuid: {voice_uuid}, emotion: {self._current_emotion})"
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            # Resemble AI uses Bearer token authentication
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                }
            )
        return self._session

    def set_voice(self, voice: str) -> None:
        """Set voice/emotion for TTS output.

        Maps voice names to emotions for Chatterbox.

        Args:
            voice: Voice name or emotion identifier
        """
        self._voice_id = voice
        self._current_emotion = VOICE_TO_EMOTION.get(voice, "neutral")
        params = EMOTION_TO_PARAMS.get(self._current_emotion, DEFAULT_PARAMS)
        logger.info(
            f"Chatterbox voice set: {voice} -> emotion={self._current_emotion} "
            f"(exaggeration={params['exaggeration']}, cfg_weight={params['cfg_weight']})"
        )

    def set_emotion(self, emotion: str) -> None:
        """Directly set emotion for TTS.

        Args:
            emotion: Emotion name (neutral, sad, frustrated, excited, etc.)
        """
        if emotion in EMOTION_TO_PARAMS:
            self._current_emotion = emotion
            params = EMOTION_TO_PARAMS[emotion]
            logger.info(
                f"Chatterbox emotion set: {emotion} "
                f"(exaggeration={params['exaggeration']}, cfg_weight={params['cfg_weight']})"
            )
        else:
            logger.warning(f"Unknown emotion '{emotion}', using neutral")
            self._current_emotion = "neutral"

    def get_emotion_params(self) -> Dict[str, float]:
        """Get Chatterbox parameters for current emotion.

        Returns:
            Dict with exaggeration and cfg_weight values
        """
        return EMOTION_TO_PARAMS.get(self._current_emotion, DEFAULT_PARAMS)

    async def run_tts(self, text: str) -> AsyncGenerator[Frame, None]:
        """Run text-to-speech synthesis with emotion control.

        This is the main method called by Pipecat pipeline.

        Args:
            text: Text to synthesize

        Yields:
            Pipecat frames (TTSStartedFrame, TTSAudioRawFrame, TTSStoppedFrame)
        """
        params = self.get_emotion_params()
        logger.info(
            f"🔊 Chatterbox TTS request: text='{text[:80]}{'...' if len(text) > 80 else ''}' "
            f"emotion={self._current_emotion} exaggeration={params['exaggeration']} "
            f"cfg_weight={params['cfg_weight']}"
        )

        try:
            # Signal TTS started
            yield TTSStartedFrame()

            payload = {
                "voice_uuid": self._voice_uuid,
                "data": text,
                "exaggeration": params["exaggeration"],
                "cfg_weight": params["cfg_weight"],
                "sample_rate": self._sample_rate,
                "precision": "PCM_16",
            }

            # Log full request details for debugging
            logger.info(
                f"🔊 Chatterbox API call: model={self._model} "
                f"voice_uuid={self._voice_uuid[:8]}...{self._voice_uuid[-4:]} "
                f"sample_rate={self._sample_rate} precision=PCM_16"
            )

            session = await self._get_session()

            # Try stream endpoint first (returns raw WAV chunks for low-latency playback)
            # Fall back to synthesis endpoint (returns JSON with base64 audio)
            for url in [self._stream_url, self._synthesis_url]:
                start_time = time.time()
                is_stream = (url == self._stream_url)

                async with session.post(url, json=payload) as response:
                    ttfb_ms = (time.time() - start_time) * 1000

                    if response.status == 500 and is_stream:
                        error_text = await response.text()
                        logger.warning(
                            f"🔊 Stream endpoint failed (500), trying synthesis... "
                            f"error={error_text[:100]}"
                        )
                        continue  # Try synthesis endpoint as fallback

                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            f"🔊 Chatterbox TTS FAILED: status={response.status} "
                            f"url={url} latency={ttfb_ms:.0f}ms error={error_text[:200]}"
                        )
                        yield ErrorFrame(f"Chatterbox TTS failed: {response.status}")
                        break

                    logger.info(
                        f"🔊 Chatterbox TTS: started via {'stream' if is_stream else 'synthesis'} "
                        f"(ttfb={ttfb_ms:.0f}ms)"
                    )

                    chunks_sent = 0
                    total_bytes = 0

                    if is_stream:
                        # Stream endpoint returns raw WAV bytes — strip header and yield chunks
                        header_stripped = False
                        header_buffer = b''

                        async for chunk in response.content.iter_chunked(16384):
                            if not chunk:
                                continue

                            total_bytes += len(chunk)

                            # Strip WAV header from first chunk(s)
                            if not header_stripped:
                                header_buffer += chunk
                                if len(header_buffer) >= 44:
                                    if header_buffer[:4] == b'RIFF':
                                        data_index = header_buffer.find(b'data')
                                        if data_index != -1:
                                            header_size = data_index + 8
                                            chunk = header_buffer[header_size:]
                                            header_stripped = True
                                            logger.debug(f"🔊 Stripped WAV header ({header_size} bytes)")
                                        else:
                                            continue
                                    else:
                                        chunk = header_buffer
                                        header_stripped = True
                                    header_buffer = b''

                            if chunk:
                                yield TTSAudioRawFrame(
                                    audio=chunk,
                                    sample_rate=self._sample_rate,
                                    num_channels=1,
                                )
                                chunks_sent += 1
                    else:
                        # Synthesis endpoint returns JSON with base64-encoded audio
                        import base64
                        import json as json_mod

                        response_text = await response.text()
                        try:
                            response_json = json_mod.loads(response_text)
                            audio_b64 = response_json.get("audio_content", "")
                            if not audio_b64:
                                logger.error("🔊 Synthesis response missing audio_content")
                                yield ErrorFrame("Chatterbox synthesis: no audio_content")
                                break

                            audio_bytes = base64.b64decode(audio_b64)
                            total_bytes = len(audio_bytes)

                            # Strip WAV header if present
                            if audio_bytes[:4] == b'RIFF':
                                data_index = audio_bytes.find(b'data')
                                if data_index != -1:
                                    header_size = data_index + 8
                                    audio_bytes = audio_bytes[header_size:]
                                    logger.debug(f"🔊 Stripped WAV header ({header_size} bytes)")

                            # Yield in chunks for smooth pipeline processing
                            chunk_size = 16384
                            for i in range(0, len(audio_bytes), chunk_size):
                                chunk = audio_bytes[i:i + chunk_size]
                                yield TTSAudioRawFrame(
                                    audio=chunk,
                                    sample_rate=self._sample_rate,
                                    num_channels=1,
                                )
                                chunks_sent += 1

                        except (json_mod.JSONDecodeError, Exception) as e:
                            logger.error(f"🔊 Failed to parse synthesis response: {e}")
                            yield ErrorFrame(f"Chatterbox synthesis parse error: {e}")
                            break

                    total_ms = (time.time() - start_time) * 1000
                    audio_duration_secs = total_bytes / (self._sample_rate * 2)
                    logger.info(
                        f"🔊 Chatterbox TTS complete: total={total_ms:.0f}ms "
                        f"audio={total_bytes} bytes ({audio_duration_secs:.1f}s) "
                        f"chunks={chunks_sent} via={'stream' if is_stream else 'synthesis'}"
                    )
                    # Emit subtitle data with exact audio duration for frontend word reveal
                    if total_bytes > 0:
                        yield RTVIServerMessageFrame(data={
                            "message_type": "subtitle_chunk",
                            "text": text,
                            "audio_duration": audio_duration_secs,
                            "timestamp": time.time(),
                        })

                    break  # Success, don't try next URL

            # Signal TTS stopped
            yield TTSStoppedFrame()
            logger.info(f"🔊 Chatterbox TTS complete for: '{text[:50]}...'")

        except aiohttp.ClientError as e:
            logger.error(f"🔊 Chatterbox API connection error: {e}")
            yield ErrorFrame(f"Chatterbox API error: {e}")
            yield TTSStoppedFrame()

        except Exception as e:
            logger.error(f"🔊 Chatterbox TTS unexpected error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            yield ErrorFrame(f"Chatterbox TTS error: {e}")
            yield TTSStoppedFrame()

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("ChatterboxTTSService session closed")
        await super().cleanup()


def create_chatterbox_tts_service(
    api_key: str,
    voice_uuid: str,
    synthesis_url: str = "https://f.cluster.resemble.ai/synthesize",
    stream_url: str = "https://f.cluster.resemble.ai/stream",
    sample_rate: int = 24000,
    model: str = "chatterbox-turbo",
    voice: str = "neutral",
) -> ChatterboxTTSService:
    """Create a Chatterbox TTS service instance.

    Args:
        api_key: Resemble AI API key
        voice_uuid: Resemble AI voice UUID
        synthesis_url: Synthesis endpoint URL
        stream_url: Streaming endpoint URL
        sample_rate: Audio sample rate
        model: Resemble model (default "chatterbox-turbo")
        voice: Initial voice/emotion

    Returns:
        ChatterboxTTSService instance
    """
    return ChatterboxTTSService(
        api_key=api_key,
        voice_uuid=voice_uuid,
        synthesis_url=synthesis_url,
        stream_url=stream_url,
        sample_rate=sample_rate,
        model=model,
        voice=voice,
    )
