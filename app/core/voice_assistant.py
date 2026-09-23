"""
Main Voice Assistant orchestrator.

This module contains the VoiceAssistant class that coordinates all services
and manages the overall voice assistant functionality including:
- Speech-to-Text processing
- Text-to-Speech synthesis
- Conversation management
- Pipeline orchestration
"""

import asyncio
from typing import Any, Dict, List

from loguru import logger
from pipecat.frames.frames import (
    TTSSpeakFrame,
    TextFrame,
    LLMFullResponseStartFrame,
    LLMFullResponseEndFrame,
    TTSUpdateSettingsFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.frameworks.rtvi import RTVIObserver, RTVIProcessor, RTVIServerMessageFrame
from pipecat.processors.aggregators.sentence import SentenceAggregator
from pipecat.transports.base_transport import BaseTransport

from app.services.conversation import ConversationManager
from app.services.input_analyzer import InputAnalyzer
from app.services.latency import LatencyAnalyzer
from app.services.stt import SpeechToTextService
from app.services.tts import TextToSpeechService
from app.processors.text_filter_processor import TextFilterProcessor
from app.processors.visual_hint_processor import VisualHintProcessor
from app.processors.smart_interruption_processor import SmartInterruptionProcessor
from app.processors.subtitle_sync_processor import SubtitleSyncProcessor


class VoiceAssistant:
    """Main Voice Assistant class that coordinates all services.

    This class orchestrates the speech-to-text, text-to-speech, input analysis,
    RAG processing, and conversation management services to provide a complete
    voice assistant experience.

    Attributes:
        config: Configuration dictionary for all services
        stt_service: Speech-to-Text service instance
        tts_service: Text-to-Speech service instance
        input_analyzer: Input analysis service
        conversation_manager: Manages conversation context and LLM
        pipeline: Pipecat processing pipeline
        task: Pipeline task
        runner: Pipeline runner
    """

    def __init__(self, config: Dict[str, Any] = None, persona_config: Dict[str, Any] = None):
        """Initialize the Voice Assistant.

        Args:
            config: Configuration dictionary containing settings for all services
            persona_config: Optional persona override (voice_id, system_prompt_override, greetings)
        """
        self.config = config or {}
        self.persona_config = persona_config

        # Initialize services
        self.stt_service = None
        self.tts_service = None
        self.input_analyzer = None
        self.conversation_manager = None

        # Pipeline components
        self.pipeline = None
        self.task = None
        self.runner = None
        self.rtvi = RTVIProcessor()
        self.latency_analyzer = LatencyAnalyzer()

        # Tone-aware processor for dynamic voice selection using MSP-PODCAST + LLM text sentiment
        # Uses Google API key for Gemini-based text sentiment detection
        # Can be disabled via config for performance testing (wav2vec2 is CPU-intensive)
        google_api_key = self.config.get("conversation", {}).get("llm", {}).get("api_key")
        server_config = self.config.get("server", {})
        emotion_enabled = server_config.get("emotion_detection_enabled", True)
        tts_config = self.config.get("tts", {}).get("config", {})
        dynamic_tts_emotion = tts_config.get("dynamic_emotion", True)
        logger.info(
            f"[EMOTION-DIAG] Emotion detection config: enabled={emotion_enabled}, "
            f"groq_api_key={'SET' if google_api_key and not google_api_key.startswith('$') else 'MISSING'}"
        )
        self.tone_processor = None
        if emotion_enabled:
            # Keep the heavy wav2vec2/PyTorch dependency completely outside the
            # production import path when emotion analysis is disabled.
            from app.processors.tone_aware_processor import ToneAwareProcessor

            self.tone_processor = ToneAwareProcessor(
                cooldown_seconds=3.0,
                enabled=True,
                tts_emotion_enabled=dynamic_tts_emotion,
                groq_api_key=google_api_key,
            )
        else:
            logger.info("Emotion detection disabled; skipping MSP-PODCAST and PyTorch")

        # Text filter processor to remove markdown before TTS.
        # inject_laughter=True only for Cartesia — it understands [laughter] tags natively.
        tts_provider_for_filter = self.config.get("tts", {}).get("provider", "elevenlabs")
        self.text_filter = TextFilterProcessor(
            enabled=True,
            inject_laughter=(tts_provider_for_filter == "cartesia"),
        )

        # Visual hint processor
        a2ui_config = self.config.get("a2ui", {})
        a2ui_enabled = a2ui_config.get("enabled", True)
        logger.info(f"🎨 A2UI system enabled (RAG-triggered only): {a2ui_enabled}")
        self.visual_hint_processor = VisualHintProcessor(
            enabled=True,
            stream_words=False,
            detect_content=False,
            use_a2ui=False,
        )

        # Subtitle sync processor - emits subtitles synced with TTS audio playback
        # Intercepts upstream TTSTextFrame (timed by transport) for perfect audio-text sync
        self.subtitle_sync = SubtitleSyncProcessor()

        # Smart interruption processor - validates interruptions to prevent false barge-ins
        smart_int_config = server_config.get("smart_interruption", {})
        smart_int_enabled = smart_int_config.get("enabled", True)
        logger.info(f"🛡️ Smart interruption validation enabled: {smart_int_enabled}")
        self.smart_interruption = SmartInterruptionProcessor(
            enabled=smart_int_enabled,
            min_confidence_threshold=smart_int_config.get("min_confidence", 0.7),
        )

        # Store LLM and context references for greeting injection
        self.llm = None
        self.context_aggregator = None

        # Track conversation ending
        self.conversation_should_end = False

        # Track if greeting has been sent (with timestamp to prevent duplicates within 5 seconds)
        self._greeting_sent_at = 0

        logger.info("Initialized Voice Assistant")

    def initialize_services(self) -> None:
        """Initialize all service components."""
        logger.info("Initializing Voice Assistant services...")

        # Initialize Speech-to-Text service
        stt_config = self.config.get("stt", {})
        stt_kwargs = stt_config.get("config", {}).copy()

        # Override STT language if persona specifies one (e.g., "multi" for Hinglish)
        if self.persona_config and self.persona_config.get("stt_language"):
            stt_kwargs["language"] = self.persona_config["stt_language"]
            logger.info(f"🎭 Persona STT language override: {self.persona_config['stt_language']}")

        self.stt_service = SpeechToTextService(
            stt_provider=stt_config.get("provider", "whisper"),
            **stt_kwargs,
        )

        # Initialize Text-to-Speech service
        tts_config = self.config.get("tts", {})
        tts_kwargs = tts_config.get("config", {}).copy()

        # Override voice_id if persona specifies one
        if self.persona_config and self.persona_config.get("voice_id"):
            persona_voice_id = self.persona_config["voice_id"]
            # Resolve ${ENV_VAR} references
            if persona_voice_id.startswith("${") and persona_voice_id.endswith("}"):
                import os
                env_var = persona_voice_id[2:-1]
                persona_voice_id = os.getenv(env_var, "")
            if persona_voice_id:
                tts_kwargs["voice_id"] = persona_voice_id
                logger.info(f"🎭 Persona voice override: voice_id={persona_voice_id[:8]}...")

        self.tts_service = TextToSpeechService(
            tts_provider=tts_config.get("provider", "elevenlabs"),
            **tts_kwargs,
        )

        # Initialize Input Analyzer
        input_config = self.config.get("input_analyzer", {})
        self.input_analyzer = InputAnalyzer(
            custom_patterns=input_config.get("custom_patterns")
        )

        # Initialize Conversation Manager
        conversation_config = self.config.get("conversation", {})
        language_config = self.config.get("language", {})
        server_config = self.config.get("server", {})

        # Include system_prompt in llm_config so ConversationManager can access it
        llm_config = conversation_config.get("llm", {}).copy()
        llm_config["system_prompt"] = conversation_config.get("system_prompt", "")
        llm_config["voice_delivery_instructions"] = conversation_config.get(
            "voice_delivery_instructions", ""
        )

        # Override system_prompt if persona has a custom one
        if self.persona_config and self.persona_config.get("system_prompt_override"):
            llm_config["system_prompt"] = self.persona_config["system_prompt_override"]
            logger.info(f"🎭 Persona system prompt override applied ({len(self.persona_config['system_prompt_override'])} chars)")

        # Determine current persona ID for agent roster
        current_persona_id = ""
        personas_config = self.config.get("personas", {})
        if self.persona_config:
            # Find the persona_id that matches this config
            for pid, pcfg in personas_config.get("agents", {}).items():
                if pcfg.get("name") == self.persona_config.get("name"):
                    current_persona_id = pid
                    break

        self.conversation_manager = ConversationManager(
            input_analyzer=self.input_analyzer,
            llm_config=llm_config,
            language_config=language_config,
            vad_config=server_config.get("vad", {}),
            personas_config=personas_config,
            current_persona_id=current_persona_id,
        )

        logger.info("All services initialized successfully")

    async def create_pipeline(self, transport: BaseTransport) -> Pipeline:
        """Create the processing pipeline.

        Args:
            transport: The transport layer for audio input/output

        Returns:
            The configured pipeline

        Raises:
            ValueError: If services are not initialized
        """
        if not self.conversation_manager:
            raise ValueError("Services must be initialized before creating pipeline")

        # Get service instances
        stt = self.stt_service.get_service()
        tts = self.tts_service.get_service()
        llm = self.conversation_manager.get_llm_service()

        # Flux advertises its external turn strategies to this aggregator.
        context_aggregator = self.conversation_manager.get_context_aggregator()

        # Store LLM, TTS and context for greeting injection
        self.llm = llm
        self.tts = tts
        self.context_aggregator = context_aggregator

        # Set up TTS service in conversation manager for function call feedback
        self.conversation_manager.set_tts_service(tts)

        # Wire up agent transfer callback for live persona switching
        self.conversation_manager.set_agent_transfer_callback(
            self._handle_agent_transfer
        )

        if self.tone_processor:
            self.tone_processor.set_tts_service(tts)
            self.tone_processor.set_visual_hint_processor(self.visual_hint_processor)
            logger.info("[EMOTION-DIAG] Initializing optional tone processor...")
            await self.tone_processor.initialize()

        # Get smart interruption config for conditional pipeline inclusion
        server_config = self.config.get("server", {})
        smart_int_config = server_config.get("smart_interruption", {})
        smart_int_enabled = smart_int_config.get("enabled", True)

        # Create pipeline
        # ToneAwareProcessor receives audio frames for SpeechBrain emotion detection
        # VisualHintProcessor streams text word-by-word and emits visual hints
        # TextFilterProcessor removes markdown before TTS

        # Build pipeline processors list
        pipeline_processors = [
            transport.input(),
            stt,                          # STT first to generate transcriptions
        ]

        # Only add SmartInterruptionProcessor if enabled
        if smart_int_enabled:
            pipeline_processors.append(self.smart_interruption)  # Validate interruptions from transcriptions
            logger.info("🛡️ SmartInterruptionProcessor added to pipeline")
        else:
            logger.info("🛡️ SmartInterruptionProcessor DISABLED - not added to pipeline")

        if self.tone_processor:
            pipeline_processors.append(self.tone_processor)

        pipeline_processors.extend([
            context_aggregator.user(),    # Context aggregator (receives only unmuted frames)
            self.rtvi,
            llm,
            self.visual_hint_processor,   # Stream text and detect content for visual cards
            self.text_filter,             # Remove markdown before TTS
            SentenceAggregator(),         # Collect text into full sentences before TTS (prevents choppy audio)
            tts,
            self.subtitle_sync,           # Sync subtitles with TTS audio via upstream TTSTextFrame
            transport.output(),
            context_aggregator.assistant(),
        ])

        self.pipeline = Pipeline(pipeline_processors)

        logger.info("Pipeline created successfully")
        return self.pipeline

    def create_task(self, enable_metrics: bool = True) -> PipelineTask:
        """Create the pipeline task.

        Args:
            enable_metrics: Whether to enable metrics collection

        Returns:
            The configured pipeline task

        Raises:
            ValueError: If pipeline is not created
        """
        if not self.pipeline:
            raise ValueError("Pipeline must be created before creating task")

        # Build pipeline params with interruption support
        pipeline_params = PipelineParams(
            enable_metrics=enable_metrics,
            enable_usage_metrics=enable_metrics,
            report_only_initial_ttfb=True,  # Only report first TTFB for cleaner metrics
        )

        logger.info("Interruption and barge-in are managed by Deepgram Flux turn events")

        self.task = PipelineTask(
            self.pipeline,
            params=pipeline_params,
            observers=[RTVIObserver(self.rtvi)],
        )

        logger.info("Pipeline task created successfully")
        return self.task

    def setup_transport_handlers(self, transport: BaseTransport) -> None:
        """Set up transport event handlers.

        Args:
            transport: The transport instance to set up handlers for

        Raises:
            ValueError: If task is not created
        """
        if not self.task:
            raise ValueError("Task must be created before setting up transport handlers")

        @transport.event_handler("on_client_connected")
        async def on_client_connected(transport, client):
            logger.info(f"✅ Client connected: {client}")

            # Wait for pipeline to be fully ready (StartFrame must be processed)
            await asyncio.sleep(1.5)
            logger.info("🎤 Pipeline ready, sending greeting...")

            # Queue greeting through the TASK so it flows through the full pipeline
            # Use persona-specific greetings if available, otherwise default
            import random
            if self.persona_config and self.persona_config.get("greetings"):
                greeting_options = self.persona_config["greetings"]
                logger.info(f"🎭 Using persona greetings ({len(greeting_options)} options)")
            else:
                greeting_options = [
                    "Hi, I'm your voice assistant. How can I help you today? ",
                    "Hey there! I'm your AI assistant. What can I help you with? ",
                    "Hi! Your voice assistant here. What would you like to explore? ",
                    "Hello! I'm your AI assistant. What would you like to know? "
                ]
            # Add trailing space to ensure last word is emitted (not buffered for next chunk)
            greeting_text = random.choice(greeting_options)

            # Send frames to properly signal utterance boundaries:
            # 1. LLMFullResponseStartFrame - initializes utterance_id
            # 2. TextFrame - the greeting text (flows through VisualHintProcessor → TTS)
            # 3. LLMFullResponseEndFrame - flushes word buffer and finalizes
            logger.info(f"🎤 Queueing greeting with utterance frames: '{greeting_text[:50]}...'")
            await self.task.queue_frame(LLMFullResponseStartFrame())
            await self.task.queue_frame(TextFrame(greeting_text))
            await self.task.queue_frame(LLMFullResponseEndFrame())
            logger.info(f"✅ Greeting frames queued successfully")

            # Add greeting to conversation context so LLM knows it already greeted
            if self.conversation_manager and self.conversation_manager.context:
                self.conversation_manager.context.messages.append(
                    {"role": "assistant", "content": greeting_text}
                )
                logger.info("📝 Greeting added to conversation context")

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, client):
            logger.info(f"Client disconnected: {client}")
            # Don't reset greeting time here - let it expire naturally after 5 seconds
            # Don't cancel task immediately - the server loop will handle cleanup
            # and restart for new connections. Cancelling here causes issues when
            # a replacement connection arrives (Pipecat closes old connection first)
            logger.debug("Client disconnected, awaiting session end")

        logger.info("Transport handlers set up successfully")

    async def run(self, transport: BaseTransport, handle_sigint: bool = True) -> None:
        """Run the voice assistant.

        Args:
            transport: The transport layer for audio input/output
            handle_sigint: Whether to handle SIGINT for graceful shutdown
        """
        logger.info("Starting Voice Assistant...")

        # Initialize services if not already done
        if not self.conversation_manager:
            logger.debug("Initializing services...")
            self.initialize_services()

        # Create pipeline and task
        logger.debug("Creating pipeline...")
        await self.create_pipeline(transport)

        logger.debug("Creating task...")
        self.create_task()

        # Set up transport handlers
        logger.debug("Setting up transport handlers...")
        self.setup_transport_handlers(transport)

        # Create and run the pipeline runner
        logger.info("Creating pipeline runner...")
        self.runner = PipelineRunner(handle_sigint=handle_sigint)
        logger.info("Starting pipeline runner...")
        await self.runner.run(self.task)

        logger.info("Voice Assistant stopped")

    async def _handle_agent_transfer(self, agent_id: str, persona_config: Dict[str, Any]) -> None:
        """Handle live agent transfer by switching TTS voice and notifying frontend.

        Args:
            agent_id: The target agent's ID
            persona_config: The target agent's configuration dict
        """
        import os

        # Resolve the new voice before publishing the handoff. Both frames are
        # queued together so the pipeline applies the voice first and the UI can
        # stage the matching identity for the next BotStartedSpeaking event.
        new_voice_id = persona_config.get("voice_id", "")
        if new_voice_id.startswith("${") and new_voice_id.endswith("}"):
            env_var = new_voice_id[2:-1]
            new_voice_id = os.getenv(env_var, "")

        agent_name = persona_config.get("name", agent_id)
        agent_role = persona_config.get("role", "Agent")
        agent_avatar = persona_config.get("avatar", "")

        transfer_message = RTVIServerMessageFrame(
            data={
                "message_type": "agent_transfer",
                "agent_id": agent_id,
                "name": agent_name,
                "role": agent_role,
                "avatar": agent_avatar,
                "apply_on_next_speech": True,
            }
        )

        if self.task:
            frames = []
            settings_class = getattr(self.tts, "Settings", None) if self.tts else None
            if new_voice_id and settings_class:
                frames.append(
                    TTSUpdateSettingsFrame(
                        delta=settings_class(voice=new_voice_id),
                        service=self.tts,
                    )
                )
            frames.append(transfer_message)
            await self.task.queue_frames(frames)
            logger.info(
                f"🔄 Staged synchronized transfer to {agent_name} "
                f"(voice={'updated' if new_voice_id and settings_class else 'unchanged'})"
            )

        # Update persona_config reference
        self.persona_config = persona_config

    def get_service_status(self) -> Dict[str, Any]:
        """Get the status of all services.

        Returns:
            Dictionary containing the status of all services
        """
        return {
            "stt_service": {
                "initialized": self.stt_service is not None,
                "config": self.stt_service.get_config() if self.stt_service else None,
            },
            "tts_service": {
                "initialized": self.tts_service is not None,
                "config": self.tts_service.get_config() if self.tts_service else None,
            },
            "input_analyzer": {
                "initialized": self.input_analyzer is not None,
                "patterns": self.input_analyzer.get_patterns() if self.input_analyzer else None,
            },
            "conversation_manager": {
                "initialized": self.conversation_manager is not None,
                "stats": (
                    self.conversation_manager.get_conversation_stats()
                    if self.conversation_manager
                    else None
                ),
            },
            "pipeline": {
                "created": self.pipeline is not None,
                "task_created": self.task is not None,
                "runner_created": self.runner is not None,
            },
            "latency_analyzer": {
                "initialized": self.latency_analyzer is not None,
                "statistics": (
                    self.latency_analyzer.get_statistics() if self.latency_analyzer else None
                ),
            },
        }

    def shutdown(self) -> None:
        """Gracefully shut down the voice assistant."""
        logger.info("Shutting down Voice Assistant...")

        if self.task:
            asyncio.create_task(self.task.cancel())

        logger.info("Voice Assistant shut down complete")

    @classmethod
    def create_from_config(cls, config_dict: Dict[str, Any]) -> "VoiceAssistant":
        """Create a VoiceAssistant instance from a configuration dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            Configured VoiceAssistant instance
        """
        instance = cls(config_dict)
        instance.initialize_services()
        return instance
