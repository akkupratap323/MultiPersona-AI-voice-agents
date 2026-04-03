"""
Visual Hint Processor - Streaming text and A2UI visual generation.

This processor intercepts LLM text output and:
1. Emits streaming_text events word-by-word for animated display
2. Uses A2UI 3-tier orchestrator to detect appropriate visual templates
3. Generates A2UI JSON for rich visual card rendering in frontend
4. Emits visual_hint events (legacy) and a2ui_update events (new)
"""

import re
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from pipecat.frames.frames import Frame, TextFrame, LLMFullResponseStartFrame, LLMFullResponseEndFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.processors.frameworks.rtvi import RTVIServerMessageFrame

# Import A2UI system
try:
    from app.services.a2ui import A2UIGenerator, detect_tier, get_tier_metadata
    A2UI_AVAILABLE = True
    logger.info("=" * 60)
    logger.info("🎨 A2UI SYSTEM IMPORTED SUCCESSFULLY")
    logger.info("=" * 60)
except ImportError as e:
    A2UI_AVAILABLE = False
    logger.warning("=" * 60)
    logger.warning(f"⚠️ A2UI system not available: {e}")
    logger.warning("   Using legacy visual hints only")
    logger.warning("=" * 60)


class VisualHintProcessor(FrameProcessor):
    """Processor that streams text word-by-word and detects content for visual hints."""

    # Content detection patterns with priorities
    CONTENT_PATTERNS: Dict[str, Dict[str, Any]] = {
        "greeting": {
            "patterns": [
                re.compile(r"\b(hello|hi|hey|welcome)\b", re.IGNORECASE),
                re.compile(r"\bgood (morning|afternoon|evening)\b", re.IGNORECASE),
                re.compile(r"\bhow can I (help|assist)\b", re.IGNORECASE),
                re.compile(r"\bI'm (the |here to |happy to )", re.IGNORECASE),
            ],
            "priority": 1,
            "visual_type": "greeting_animation",
            "cooldown": 30.0,
        },
        "contact": {
            "patterns": [
                re.compile(r"[\w\.-]+@[\w\.-]+\.\w+"),  # Email
                re.compile(r"\+?1?\s*\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}"),  # Phone
                re.compile(r"\b(email|phone|call|contact|reach)\s*(us|me|them)?\s*(at|:)?\b", re.IGNORECASE),
                re.compile(r"\bget in touch\b", re.IGNORECASE),
                re.compile(r"\blet's talk\b", re.IGNORECASE),
            ],
            "priority": 2,
            "visual_type": "contact_card",
            "cooldown": 10.0,
        },
        "company": {
            "patterns": [
                re.compile(r"\b(about|tell me about|what is|who is)\s+(the company|us|you|your company)\b", re.IGNORECASE),
            ],
            "priority": 3,
            "visual_type": "company_card",
            "cooldown": 20.0,
        },
        "services": {
            "patterns": [
                re.compile(r"\b(what|describe|tell me about)\s+(your\s+)?(services?|offerings?)\b", re.IGNORECASE),
                re.compile(r"\bfour pillars\b", re.IGNORECASE),
                re.compile(r"\b(HUMAN|INTELLIGENCE|MEMORY|CLOUD)\s+pillar\b", re.IGNORECASE),
                re.compile(r"\bour\s+services?\s+(include|are|cover)\b", re.IGNORECASE),
            ],
            "priority": 4,
            "visual_type": "service_card",
            "cooldown": 15.0,
        },
        "expertise": {
            "patterns": [
                re.compile(r"\b(what|tell me about|describe)\s+(your\s+|the\s+)?(expertise|capabilities|specializations?|technical skills?)\b", re.IGNORECASE),
                re.compile(r"\b(what do you|what does the team)\s+(specialize in|excel at|focus on)\b", re.IGNORECASE),
                re.compile(r"\b(our|the|your)\s+(expertise|specialization)\s+(is|includes?|covers?)\b", re.IGNORECASE),
                re.compile(r"\bexpertise\s+(areas?|in)\s+(voice AI|agentic AI|RAG|NLP|conversational)\b", re.IGNORECASE),
            ],
            "priority": 5,
            "visual_type": "expertise_card",
            "cooldown": 15.0,
        },
        "pricing": {
            "patterns": [
                re.compile(r"\b(what|tell me about|how much)\s+(is|are|does)\s+(your\s+)?(pricing|cost|rate)\b", re.IGNORECASE),
                re.compile(r"\bengagement\s+(models?|options?|types?)\b", re.IGNORECASE),
                re.compile(r"\b(discovery|design sprint|product development)\s+(engagement|model|option)\b", re.IGNORECASE),
                re.compile(r"\bhow do you charge\b", re.IGNORECASE),
                re.compile(r"\bwhat.s (the|your) (pricing|cost|rate)\b", re.IGNORECASE),
            ],
            "priority": 6,
            "visual_type": "pricing_card",
            "cooldown": 15.0,
        },
        "project_visualizing_intelligence": {
            "patterns": [
                re.compile(r"\bvisuali[sz]ing intelligence\b", re.IGNORECASE),
                re.compile(r"\bstrategy,? identity(,| and) web\b", re.IGNORECASE),
            ],
            "priority": 7,
            "visual_type": "project_detail_visualizing_intelligence",
            "cooldown": 12.0,
        },
        "project_natural_conversations": {
            "patterns": [
                re.compile(r"\bnatural conversations( with data)?\b", re.IGNORECASE),
                re.compile(r"\bconversations with data\b", re.IGNORECASE),
                re.compile(r"\bplain language (data|analytics)\b", re.IGNORECASE),
                re.compile(r"\bdata platform\b", re.IGNORECASE),
            ],
            "priority": 7,
            "visual_type": "project_detail_natural_conversations",
            "cooldown": 12.0,
        },
        "project_agentic_intake": {
            "patterns": [
                re.compile(r"\bagentic intake coordinator\b", re.IGNORECASE),
                re.compile(r"\bintake coordinator\b", re.IGNORECASE),
                re.compile(r"\bintake workflow\b", re.IGNORECASE),
                re.compile(r"\bworkflow automation\b", re.IGNORECASE),
            ],
            "priority": 7,
            "visual_type": "project_detail_agentic_intake",
            "cooldown": 12.0,
        },
        "project_ai_first_bank": {
            "patterns": [
                re.compile(r"\bAI[- ]?first bank\b", re.IGNORECASE),
                re.compile(r"\bconversational finance\b", re.IGNORECASE),
                re.compile(r"\bbanking experience\b", re.IGNORECASE),
            ],
            "priority": 7,
            "visual_type": "project_detail_ai_first_bank",
            "cooldown": 12.0,
        },
        "projects": {
            "patterns": [
                re.compile(r"\b(what|tell me about|show me|describe)\s+(your\s+)?(projects?|case studies?|portfolio|work|examples?)\b", re.IGNORECASE),
                re.compile(r"\bour\s+(projects?|case studies?|portfolio)\s+(include|are)\b", re.IGNORECASE),
                re.compile(r"\b(we|we've|we have)\s+(worked on|built|developed|created|delivered|completed)\s+(projects?|case studies?)\b", re.IGNORECASE),
                re.compile(r"\b(past|previous|recent)\s+(projects?|work|case studies?)\b", re.IGNORECASE),
            ],
            "priority": 8,
            "visual_type": "project_card",
            "cooldown": 15.0,
        },
        "next_steps": {
            "patterns": [
                re.compile(r"\b(what are the|what's the|tell me about the)\s+next steps?\b", re.IGNORECASE),
                re.compile(r"\bwhat happens\s+(next|after|when I reach out)\b", re.IGNORECASE),
                re.compile(r"\bhow (do I|to)\s+(start|get started|begin|proceed)\b", re.IGNORECASE),
                re.compile(r"\b(ready to|want to|like to)\s+(start|begin|get started|move forward)\b", re.IGNORECASE),
                re.compile(r"\b(process|timeline|engagement)\s+(for|when)\s+(starting|onboarding|beginning)\b", re.IGNORECASE),
            ],
            "priority": 8,
            "visual_type": "next_steps_card",
            "cooldown": 20.0,
        },
        "location": {
            "patterns": [
                re.compile(r"\b(what is your|where is your|where are you)\s+(location|address|office)\b", re.IGNORECASE),
                re.compile(r"\b(where|how)\s+(can I|do I)\s+(visit|find you|come see you)\b", re.IGNORECASE),
                re.compile(r"\bin.person\s+(meeting|visit)\b", re.IGNORECASE),
            ],
            "priority": 9,
            "visual_type": "location_card",
            "cooldown": 20.0,
        },
    }

    # Patterns for extracting specific content
    EMAIL_PATTERN = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
    PHONE_PATTERN = re.compile(r"\+?1?\s*\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")

    def __init__(
        self,
        enabled: bool = True,
        stream_words: bool = True,
        detect_content: bool = True,
        min_confidence: float = 0.5,  # Increased threshold for more precise triggering
        use_a2ui: bool = True,  # Enable A2UI system for visual generation
        **kwargs
    ):
        """Initialize the Visual Hint Processor.

        Args:
            enabled: Whether the processor is enabled
            stream_words: Whether to emit streaming text events
            detect_content: Whether to detect content for visual hints
            min_confidence: Minimum confidence for content detection
            use_a2ui: Enable A2UI 3-tier visual generation system
        """
        super().__init__(**kwargs)
        self.enabled = enabled
        self.stream_words = stream_words
        self.detect_content = detect_content
        self.min_confidence = min_confidence
        self.use_a2ui = use_a2ui and A2UI_AVAILABLE

        # Initialize A2UI generator if enabled
        self._a2ui_generator: Optional[A2UIGenerator] = None
        if self.use_a2ui:
            logger.info("🎨 Initializing A2UI Generator...")
            self._a2ui_generator = A2UIGenerator(enabled=True)
            logger.info("✅ A2UI Generator initialized successfully")
            logger.info("   A2UI will generate visual cards from LLM responses")
        else:
            logger.info("⚠️ A2UI Generator NOT initialized (use_a2ui=False or not available)")

        # State tracking
        self._current_utterance_id: Optional[str] = None
        self._sequence_counter: int = 0
        self._text_buffer: str = ""
        self._word_buffer: str = ""  # Holds partial word across chunk boundaries
        self._current_query: str = ""  # Store the user's query for A2UI
        self._last_hint_times: Dict[str, float] = {}  # Track cooldowns per content type
        self._emitted_hints_this_utterance: set = set()  # Prevent duplicate hints
        self._a2ui_emitted_this_utterance: bool = False  # Prevent duplicate A2UI

        logger.info(
            f"VisualHintProcessor initialized: "
            f"enabled={enabled}, stream_words={stream_words}, detect_content={detect_content}, "
            f"use_a2ui={self.use_a2ui}"
        )

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process frames, intercepting TextFrames for streaming and content detection."""
        await super().process_frame(frame, direction)

        if not self.enabled:
            await self.push_frame(frame, direction)
            return

        if direction == FrameDirection.DOWNSTREAM:
            # New LLM response starting — reset utterance state
            if isinstance(frame, LLMFullResponseStartFrame):
                self._current_utterance_id = str(uuid.uuid4())
                self._sequence_counter = 0
                self._text_buffer = ""
                self._word_buffer = ""
                self._emitted_hints_this_utterance = set()
                self._a2ui_emitted_this_utterance = False
                logger.info(f"📝 LLMFullResponseStart → new utterance: {self._current_utterance_id}")

            # LLM response finished — flush any partial word and finalize
            elif isinstance(frame, LLMFullResponseEndFrame):
                if self.stream_words and self._word_buffer:
                    # Flush the leftover partial word
                    self._sequence_counter += 1
                    await self._emit_word(self._word_buffer, self._sequence_counter)
                    self._word_buffer = ""
                await self.finalize_utterance()
                logger.info(f"📝 LLMFullResponseEnd → utterance finalized")

            # Stream text chunks word-by-word
            elif isinstance(frame, TextFrame):
                text = frame.text if hasattr(frame, 'text') else str(frame)
                logger.info(f"📝 [SUBTITLE] TextFrame received: '{text[:80]}...' (len={len(text)}, stream_words={self.stream_words})")
                if text and text.strip():
                    if self.stream_words:
                        logger.info(f"📤 [SUBTITLE] Emitting streaming text for: '{text[:50]}...'")
                        await self._emit_streaming_text(text)

                    # Buffer full text for content detection
                    self._text_buffer += text

                    if self.detect_content:
                        await self._detect_and_emit_hints()

        # Always pass frame downstream to TTS
        if isinstance(frame, TextFrame):
            logger.info(f"➡️ [SUBTITLE] Passing TextFrame downstream to TTS: '{frame.text[:50] if hasattr(frame, 'text') else str(frame)[:50]}...'")
        await self.push_frame(frame, direction)

    async def _emit_streaming_text(self, text: str) -> None:
        """Emit streaming text event for word-by-word display.

        LLM streaming chunks do not respect word boundaries — a word like
        "Acknowledged" may arrive as "Acknowled" + "ged" across two chunks.
        We buffer the trailing partial word and prepend it to the next chunk.

        Args:
            text: Text chunk from LLM
        """
        # Initialize utterance_id if not set (e.g., for greeting messages)
        if self._current_utterance_id is None:
            self._current_utterance_id = str(uuid.uuid4())
            self._sequence_counter = 0
            logger.info(f"🆔 [SUBTITLE] Generated new utterance_id: {self._current_utterance_id[:8]}")

        # Prepend any leftover partial word from the previous chunk
        text = self._word_buffer + text
        self._word_buffer = ""

        # If the chunk does NOT end with whitespace, the last token is a
        # partial word — hold it back until the next chunk completes it.
        if text and not text[-1].isspace():
            # Split off everything after the last space
            last_space = text.rfind(' ')
            if last_space == -1:
                # Entire chunk is one partial word — buffer it all
                self._word_buffer = text
                return
            else:
                self._word_buffer = text[last_space + 1:]
                text = text[:last_space + 1]

        # Now split the complete portion into words and emit each
        words = text.split()
        for word in words:
            if word.strip():
                self._sequence_counter += 1
                await self._emit_word(word, self._sequence_counter)

    async def _emit_word(self, word: str, seq: int) -> None:
        """Emit a single word as a streaming_text event."""
        message_data = {
            "message_type": "streaming_text",
            "text": word,
            "is_final": False,
            "sequence_id": seq,
            "utterance_id": self._current_utterance_id,
            "timestamp": time.time(),
        }
        try:
            data_frame = RTVIServerMessageFrame(data=message_data)
            await self.push_frame(data_frame)
            utterance_short = self._current_utterance_id[:8] if self._current_utterance_id else "None"
            logger.info(f"📤 [SUBTITLE] Streamed word to client: '{word}' (seq={seq}, utterance={utterance_short})")
        except Exception as e:
            logger.error(f"❌ [SUBTITLE] Failed to emit streaming text: {e}", exc_info=True)

    async def _detect_and_emit_hints(self) -> None:
        """Detect content patterns in buffered text and emit visual hints."""
        current_time = time.time()

        # Check each content type
        detected_types: List[Tuple[str, float, Dict[str, Any]]] = []

        logger.debug(f"🔍 Checking patterns in buffer: '{self._text_buffer[:100]}...'")

        for content_type, config in self.CONTENT_PATTERNS.items():
            # Skip if already emitted this utterance
            if content_type in self._emitted_hints_this_utterance:
                logger.debug(f"⏭️ Skipping {content_type} - already emitted this utterance")
                continue

            # Check cooldown
            last_time = self._last_hint_times.get(content_type, 0)
            if current_time - last_time < config["cooldown"]:
                logger.debug(f"⏭️ Skipping {content_type} - in cooldown")
                continue

            # Check patterns
            match_count = 0
            for pattern in config["patterns"]:
                if pattern.search(self._text_buffer):
                    match_count += 1

            # Calculate confidence based on match count - lowered threshold
            if match_count > 0:
                confidence = min(1.0, match_count * 0.5)  # 0.5 per match, max 1.0
                logger.info(f"📊 {content_type}: {match_count} matches, confidence={confidence:.2f}")

                if confidence >= self.min_confidence:
                    # Extract content specific to this type
                    extracted_content = self._extract_content(content_type, self._text_buffer)
                    detected_types.append((content_type, confidence, extracted_content))
                    logger.info(f"✅ {content_type} added to detected types")

        # Emit highest priority hint
        if detected_types:
            # Sort by priority (lower = higher priority)
            detected_types.sort(
                key=lambda x: self.CONTENT_PATTERNS[x[0]]["priority"]
            )

            content_type, confidence, extracted_content = detected_types[0]
            logger.info(f"🎯 Emitting visual hint: {content_type} (confidence={confidence:.2f})")
            await self._emit_visual_hint(content_type, confidence, extracted_content)

            # Mark as emitted
            self._emitted_hints_this_utterance.add(content_type)
            self._last_hint_times[content_type] = current_time
        else:
            logger.debug(f"❌ No visual hints detected (buffer len={len(self._text_buffer)})")

    def _extract_content(self, content_type: str, text: str) -> Dict[str, Any]:
        """Extract specific content based on content type.

        Args:
            content_type: Type of content to extract
            text: Text to extract from

        Returns:
            Dictionary of extracted content
        """
        content: Dict[str, Any] = {}

        if content_type == "contact":
            # Extract email
            email_match = self.EMAIL_PATTERN.search(text)
            if email_match:
                content["email"] = email_match.group()

            # Extract phone
            phone_match = self.PHONE_PATTERN.search(text)
            if phone_match:
                content["phone"] = phone_match.group()

        elif content_type == "services":
            # Extract mentioned services/capabilities
            services = []
            service_keywords = [
                "AI", "machine learning", "development", "consulting",
                "voice", "chatbot", "automation", "integration"
            ]
            for keyword in service_keywords:
                if keyword.lower() in text.lower():
                    services.append(keyword)
            if services:
                content["services"] = services[:5]  # Max 5 services

        elif content_type == "pricing":
            # Extract dollar amounts
            amounts = re.findall(r"\$[\d,]+(?:\.\d{2})?", text)
            if amounts:
                content["amounts"] = amounts

        elif content_type == "greeting":
            # No specific extraction needed
            content["type"] = "welcome"

        elif content_type.startswith("project_"):
            project_id = content_type.replace("project_", "")
            content["project_id"] = project_id
        elif content_type == "projects":
            # Extract project-related keywords
            content["mentioned"] = True

        return content

    async def _emit_visual_hint(
        self,
        content_type: str,
        confidence: float,
        content: Dict[str, Any]
    ) -> None:
        """Emit a visual hint event to the frontend.

        Args:
            content_type: Type of content detected
            confidence: Detection confidence (0-1)
            content: Extracted content data
        """
        visual_type = self.CONTENT_PATTERNS[content_type]["visual_type"]

        message_data = {
            "message_type": "visual_hint",
            "hint_type": visual_type,
            "content_type": content_type,
            "content": content,
            "confidence": round(confidence, 2),
            "trigger_text": self._text_buffer[-200:] if len(self._text_buffer) > 200 else self._text_buffer,
            "timestamp": time.time(),
        }

        logger.info(
            f"Emitting visual hint: type={visual_type}, confidence={confidence:.2f}, "
            f"content={content}"
        )

        try:
            data_frame = RTVIServerMessageFrame(data=message_data)
            await self.push_frame(data_frame)
        except Exception as e:
            logger.warning(f"Failed to emit visual hint: {e}")

    async def finalize_utterance(self) -> None:
        """Finalize the current utterance, emitting is_final=True."""
        if self._current_utterance_id:
            # Flush any remaining buffered word first
            if self.stream_words and self._word_buffer:
                self._sequence_counter += 1
                await self._emit_word(self._word_buffer, self._sequence_counter)
                self._word_buffer = ""
                logger.info(f"🔚 [SUBTITLE] Flushed final buffered word during finalization")

            # Emit final marker
            message_data = {
                "message_type": "streaming_text",
                "text": "",
                "is_final": True,
                "sequence_id": self._sequence_counter + 1,
                "utterance_id": self._current_utterance_id,
                "timestamp": time.time(),
            }

            try:
                data_frame = RTVIServerMessageFrame(data=message_data)
                await self.push_frame(data_frame)
            except Exception as e:
                logger.warning(f"Failed to emit final marker: {e}")

            logger.debug(
                f"Finalized utterance {self._current_utterance_id} "
                f"with {self._sequence_counter} words"
            )

            # Reset state
            self._current_utterance_id = None
            self._sequence_counter = 0
            self._text_buffer = ""
            self._emitted_hints_this_utterance = set()
            self._a2ui_emitted_this_utterance = False

    def set_current_query(self, query: str) -> None:
        """Set the current user query for A2UI generation.

        Call this when a new user query is received, before LLM response.

        Args:
            query: The user's question/query text
        """
        self._current_query = query
        self._a2ui_emitted_this_utterance = False
        logger.debug(f"Set current query for A2UI: {query[:50]}...")

    async def _generate_and_emit_a2ui(self) -> None:
        """Generate A2UI visual component and emit to frontend.

        Called when enough text has been buffered to generate a meaningful visual.
        """
        logger.debug("🎨 _generate_and_emit_a2ui called")
        logger.debug(f"   use_a2ui: {self.use_a2ui}")
        logger.debug(f"   generator exists: {self._a2ui_generator is not None}")
        logger.debug(f"   already emitted: {self._a2ui_emitted_this_utterance}")
        logger.debug(f"   buffer length: {len(self._text_buffer)}")
        
        if not self.use_a2ui or not self._a2ui_generator:
            logger.debug("   ⏭️ Skipping: A2UI not enabled or generator not available")
            return

        if self._a2ui_emitted_this_utterance:
            logger.debug("   ⏭️ Skipping: A2UI already emitted for this utterance")
            return

        # Only generate if we have enough context
        if len(self._text_buffer) < 50:
            logger.debug(f"   ⏭️ Skipping: Buffer too small ({len(self._text_buffer)} < 50)")
            return

        # Generate A2UI document
        logger.info("=" * 60)
        logger.info("🎨 A2UI GENERATION TRIGGERED")
        logger.info(f"   Query: '{self._current_query[:50] if self._current_query else 'N/A'}...'")
        logger.info(f"   Buffer: {len(self._text_buffer)} chars")
        logger.info("=" * 60)
        
        try:
            a2ui_doc = self._a2ui_generator.generate(
                query=self._current_query or "Information",
                llm_response=self._text_buffer
            )

            if a2ui_doc:
                logger.info("✅ A2UI document generated successfully!")
                logger.info(f"   Template: {a2ui_doc.get('root', {}).get('type', 'unknown')}")
                logger.info(f"   Tier: {a2ui_doc.get('_metadata', {}).get('tier_name', 'unknown')}")
                await self._emit_a2ui_update(a2ui_doc)
                self._a2ui_emitted_this_utterance = True
            else:
                logger.warning("⚠️ A2UI generator returned None")

        except Exception as e:
            logger.error(f"❌ A2UI generation failed: {e}")
            import traceback
            logger.error(traceback.format_exc())

    async def _emit_a2ui_update(self, a2ui_doc: Dict[str, Any]) -> None:
        """Emit A2UI update event to frontend.

        Args:
            a2ui_doc: A2UI document structure
        """
        logger.info("📤 EMITTING A2UI UPDATE TO FRONTEND")
        
        message_data = {
            "message_type": "a2ui_update",
            "a2ui": a2ui_doc,
            "utterance_id": self._current_utterance_id,
            "timestamp": time.time(),
        }

        template_type = a2ui_doc.get('root', {}).get('type', 'unknown')
        tier = a2ui_doc.get('_metadata', {}).get('tier', 'unknown')
        tier_name = a2ui_doc.get('_metadata', {}).get('tier_name', 'unknown')

        logger.info(f"   Message type: a2ui_update")
        logger.info(f"   Template: {template_type}")
        logger.info(f"   Tier: {tier} ({tier_name})")
        logger.info(f"   Utterance ID: {self._current_utterance_id}")

        try:
            data_frame = RTVIServerMessageFrame(data=message_data)
            await self.push_frame(data_frame)
            logger.info("✅ A2UI update pushed to transport successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to emit A2UI update: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def get_status(self) -> Dict[str, Any]:
        """Get processor status.

        Returns:
            Status dictionary
        """
        return {
            "enabled": self.enabled,
            "stream_words": self.stream_words,
            "detect_content": self.detect_content,
            "use_a2ui": self.use_a2ui,
            "current_utterance_id": self._current_utterance_id,
            "sequence_counter": self._sequence_counter,
            "buffer_length": len(self._text_buffer),
            "current_query": self._current_query[:50] if self._current_query else None,
            "content_types": list(self.CONTENT_PATTERNS.keys()),
        }
