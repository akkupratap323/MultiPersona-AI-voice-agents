"""
WebSocket endpoint handler for FastAPI.

This module provides the WebSocket endpoint for real-time voice communication
supporting multiple concurrent user connections with capacity management.

Features:
- Optional noise suppression (configurable)
- ai-coustics AIC speech enhancement (noise reduction + clarity)
- SmartTurn v3 ML-based end-of-turn detection
- Emotion detection via MSP-PODCAST + Gemini
"""

import os
import uuid
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger


async def websocket_endpoint(websocket: WebSocket) -> None:
    """FastAPI WebSocket endpoint for Voice Assistant with concurrent connection support.

    This endpoint handles multiple WebSocket connections simultaneously with:
    - Connection capacity limits (20 max for Lightsail)
    - Session tracking and management
    - Heartbeat monitoring for stale connections
    - Isolated VoiceAssistant instance per connection
    - SmartTurn v3 ML-based end-of-turn detection
    - Optional noise suppression (configurable)
    - ai-coustics AIC speech enhancement (optional)

    Args:
        websocket: FastAPI WebSocket connection
    """
    session_id = str(uuid.uuid4())[:8]
    logger.info(f"[Session {session_id}] New WebSocket connection attempt")

    # Read persona_id from WebSocket query params (appended by /connect endpoint)
    persona_id = websocket.query_params.get("persona_id", "")
    if persona_id:
        logger.info(f"[Session {session_id}] Persona requested: {persona_id}")

    # Import connection manager
    from app.core.connection_manager import connection_manager

    # Try to accept connection (may reject if at capacity)
    await connection_manager.connect(websocket, session_id)

    # If we reach here, connection was accepted
    try:
        # Import here to avoid circular imports
        from app.core.server import voice_assistant_server
        from app.core.voice_assistant import VoiceAssistant
        from pipecat.transports.websocket.fastapi import FastAPIWebsocketTransport
        from pipecat.transports.websocket.fastapi import FastAPIWebsocketParams
        from pipecat.serializers.protobuf import ProtobufFrameSerializer
        from pipecat.audio.vad.silero import SileroVADAnalyzer
        from pipecat.audio.vad.vad_analyzer import VADParams
        # MinWordsInterruptionStrategy moved to voice_assistant.py (PipelineParams level)

        # Get configuration from config.yaml
        # Note: server_config from voice_assistant_server may not have all keys if initialized
        # before config was loaded, so read directly from full config
        full_config = voice_assistant_server.config or {}
        server_config = full_config.get("server", {})
        vad_config = server_config.get("vad", {})
        interruption_config = server_config.get("interruption", {})
        koala_config = full_config.get("noise_suppression", {})
        aic_config = full_config.get("speech_enhancement", {})

        # Log raw config to debug why config values aren't being applied
        logger.info(f"[Session {session_id}] 📋 Raw server_config keys: {list(server_config.keys())}")
        logger.info(f"[Session {session_id}] 📋 Raw vad_config: {vad_config}")
        logger.info(f"[Session {session_id}] 📋 Noise suppression config: {koala_config}")
        logger.info(f"[Session {session_id}] 📋 Speech enhancement config: {aic_config}")

        # ===== AUDIO FILTER CONFIGURATION =====
        # Noise suppression is currently disabled in config.yaml
        # AIC speech enhancement is also disabled (SDK version mismatch)
        audio_filters = []

        # ===== NOISE SUPPRESSION (Optional) =====
        noise_enabled = koala_config.get("enabled", False)
        noise_provider = koala_config.get("provider", "none")

        if noise_enabled and noise_provider != "none":
            logger.info(f"[Session {session_id}] 🔇 Noise suppression: {noise_provider.upper()} (enabled)")
        else:
            logger.info(f"[Session {session_id}] 🔇 Noise suppression: DISABLED (raw audio input)")

        # ===== AI-COUSTICS AIC SPEECH ENHANCEMENT (Step 2) =====
        # Noise reduction + speech clarity improvement
        if aic_config.get("enabled", False):
            try:
                from pipecat.audio.filters.aic_filter import AICFilter

                # Get config values
                aic_params = aic_config.get("config", {})
                license_key = aic_params.get("license_key", "")

                # Resolve environment variable if needed
                if license_key.startswith("${") and license_key.endswith("}"):
                    env_var = license_key[2:-1]
                    license_key = os.getenv(env_var, "")

                if license_key:
                    aic_filter = AICFilter(
                        license_key=license_key,
                        model_type=aic_params.get("model_type", 0),
                        enhancement_level=aic_params.get("enhancement_level", 1.0),
                        voice_gain=aic_params.get("voice_gain", 1.0),
                        noise_gate_enable=aic_params.get("noise_gate_enable", True),
                    )
                    audio_filters.append(("AIC", aic_filter))
                    logger.info(
                        f"[Session {session_id}] 🔊 AIC speech enhancement ENABLED "
                        f"(Step 2: Enhance clarity, level={aic_params.get('enhancement_level', 1.0)})"
                    )
                else:
                    logger.warning(f"[Session {session_id}] ⚠️ AIC license key not found, speech enhancement disabled")
            except ImportError:
                logger.warning(f"[Session {session_id}] ⚠️ AIC not installed. Run: pip install 'pipecat-ai[aic]'")
            except Exception as e:
                logger.error(f"[Session {session_id}] ❌ Failed to initialize AIC: {e}")

        # Select filter(s) to use
        # NOTE: Pipecat transport only supports single audio_in_filter
        # Priority: AIC (includes noise reduction) > Krisp VIVA (noise cancellation only)
        # For best quality: use AIC alone (it does both noise reduction + enhancement)
        audio_in_filter = None
        if len(audio_filters) > 1:
            # Multiple filters enabled: Use AIC (it includes noise reduction)
            # AIC provides both noise suppression AND speech enhancement
            filter_name, filter_instance = audio_filters[1]  # AIC is second (index 1)
            audio_in_filter = filter_instance
            logger.info(
                f"[Session {session_id}] 🔗 Using AIC (includes noise reduction + speech enhancement)\n"
                f"  Note: AIC provides both features, so Krisp VIVA is redundant"
            )
        elif len(audio_filters) == 1:
            # Single filter
            filter_name, filter_instance = audio_filters[0]
            audio_in_filter = filter_instance
            logger.info(f"[Session {session_id}] 🎚️ Single audio filter: {filter_name}")
        else:
            # No filters
            logger.warning(f"[Session {session_id}] ⚠️ No audio filters enabled - raw audio will be used")

        # Stricter VAD settings to prevent false barge-ins from background noise
        # MinWordsInterruptionStrategy (below) provides additional filtering
        vad_params = VADParams(
            confidence=vad_config.get("confidence", 0.7),     # HIGHER - only trigger on clear speech
            start_secs=vad_config.get("start_secs", 0.5),      # SLOWER - require 500ms of speech (filters noise)
            stop_secs=vad_config.get("stop_secs", 1.0),        # Wait 1s of silence before ending utterance
            min_volume=vad_config.get("min_volume", 0.65),     # HIGHER - ignore quiet background noise
        )
        vad_analyzer = SileroVADAnalyzer(params=vad_params)

        # Interruption strategy is configured in voice_assistant.py via PipelineParams
        # (MinWordsInterruptionStrategy is a pipeline-level param, not transport-level)

        # Register VAD analyzer for runtime parameter changes (noise cancellation toggle)
        connection_manager.register_vad_analyzer(session_id, vad_analyzer)

        logger.info(
            f"[Session {session_id}] 🎤 VAD configured: confidence={vad_params.confidence}, "
            f"start_secs={vad_params.start_secs}, stop_secs={vad_params.stop_secs}, "
            f"min_volume={vad_params.min_volume}"
        )

        # ===== SMARTTURN V3 - Configured at transport level (pipecat 0.0.98) =====
        smart_turn_config = server_config.get("smart_turn", {})
        turn_analyzer = None
        if smart_turn_config.get("enabled", False):
            try:
                from app.processors.logging_turn_analyzer import LoggingSmartTurnAnalyzer
                cpu_count = smart_turn_config.get("cpu_count", 1)
                turn_analyzer = LoggingSmartTurnAnalyzer(
                    cpu_count=cpu_count,
                    session_id=session_id
                )
                logger.info(f"[Session {session_id}] 🧠 SmartTurn v3: ENABLED at transport level (ONNX ML model)")
            except Exception as e:
                logger.error(f"[Session {session_id}] 🧠 SmartTurn v3: Failed to initialize: {e}")
                logger.info(f"[Session {session_id}] 🧠 Falling back to transcription-based detection")
        else:
            logger.info(f"[Session {session_id}] 🧠 SmartTurn v3: DISABLED (using transcription-based detection)")

        # Create transport parameters for this connection
        transport_params = FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            vad_enabled=True,
            vad_analyzer=vad_analyzer,
            vad_audio_passthrough=True,
            serializer=ProtobufFrameSerializer(),
            audio_in_filter=audio_in_filter,  # AIC or Koala (single filter only)
            audio_in_sample_rate=16000,  # Koala/AIC require 16 kHz input
            audio_out_sample_rate=24000,  # Chatterbox TTS outputs 24 kHz
            turn_analyzer=turn_analyzer,  # SmartTurn v3 ML-based end-of-turn detection
        )

        # Build filter description for logging
        if len(audio_filters) > 1:
            # Both enabled: using AIC (which includes noise reduction)
            filter_desc = f"AIC only (Koala disabled - AIC includes noise reduction)"
        elif len(audio_filters) == 1:
            filter_desc = audio_filters[0][0]
        else:
            filter_desc = "None (raw audio)"

        logger.info(f"[Session {session_id}] 🔧 Transport configured with audio filter")

        # Create transport for this specific connection
        transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=transport_params,
        )

        # Look up persona config if persona_id was provided
        persona_config = None
        if persona_id:
            personas = full_config.get("personas", {}).get("agents", {})
            if persona_id in personas:
                persona_config = personas[persona_id]
                logger.info(f"[Session {session_id}] Loaded persona: {persona_config.get('name', persona_id)} (voice_id={'SET' if persona_config.get('voice_id') else 'DEFAULT'})")
            else:
                logger.warning(f"[Session {session_id}] Persona '{persona_id}' not found, using default")

        # Create dedicated VoiceAssistant instance for this session
        voice_assistant = VoiceAssistant(voice_assistant_server.config, persona_config=persona_config)
        logger.info(f"[Session {session_id}] VoiceAssistant instance created")

        # Log emotion detection state for this session
        emotion_enabled = server_config.get("emotion_detection_enabled", True)
        logger.info(
            f"[Session {session_id}] [EMOTION-DIAG] Session emotion config: "
            f"enabled={emotion_enabled}, "
            f"tone_processor_enabled={voice_assistant.tone_processor.enabled}, "
            f"hybrid_mode={voice_assistant.tone_processor.use_hybrid_mode}"
        )

        # Log complete audio processing pipeline
        smart_turn_desc = "SmartTurn v3 (transport)" if turn_analyzer else "Transcription-based"
        logger.info(
            f"[Session {session_id}] 📊 AUDIO PIPELINE SUMMARY:\n"
            f"  ┌─ Input: Microphone (16kHz)\n"
            f"  ├─ Filters: {filter_desc}\n"
            f"  ├─ VAD: Silero (conf={vad_params.confidence}, start={vad_params.start_secs}s, vol={vad_params.min_volume})\n"
            f"  ├─ Turn Detection: {smart_turn_desc}\n"
            f"  ├─ STT Mute: ALWAYS (blocks VAD/STT during bot speech)\n"
            f"  ├─ STT: Deepgram Nova-3\n"
            f"  ├─ LLM: Groq Llama-3.3-70b\n"
            f"  └─ TTS: ElevenLabs (24kHz)"
        )

        # Run the voice assistant pipeline for this connection
        # This will block until the connection closes
        await voice_assistant.run(transport, handle_sigint=False)

        logger.info(f"[Session {session_id}] Session completed normally")

    except WebSocketDisconnect:
        logger.info(f"[Session {session_id}] Client disconnected")
    except Exception as e:
        logger.error(f"[Session {session_id}] Exception in WebSocket endpoint: {e}")
    finally:
        # Clean up connection in manager
        connection_manager.disconnect(session_id)
        logger.info(
            f"[Session {session_id}] Connection closed. "
            f"Active sessions: {connection_manager.get_active_session_count()}"
        )
