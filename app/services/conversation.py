"""Conversation Manager for the Voice Assistant.

This module orchestrates the conversation flow and manages LLM interactions.
"""

import re
from typing import Any, Callable, Dict, List, Optional

from loguru import logger
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.frames.frames import TTSSpeakFrame, EndFrame
from pipecat.processors.frame_processor import FrameDirection
from pipecat.services.google.llm import GoogleLLMService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.llm_service import FunctionCallParams, LLMService

# Universal context system (pipecat 0.0.98)
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
    LLMAssistantAggregatorParams,
)

from app.services.input_analyzer import InputAnalyzer
from app.services.groq_llm_service import GroqLLMService
from app.services.tally_submission import TallySubmissionService
from app.utils.validation import validate_email, spell_out_email

# SmartTurn v3 - ML-based end-of-turn detection (optional)
# Use LoggingSmartTurnAnalyzer wrapper for detailed turn detection logs
try:
    from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3
    from app.processors.logging_turn_analyzer import LoggingSmartTurnAnalyzer
    SMART_TURN_AVAILABLE = True
except ImportError:
    SMART_TURN_AVAILABLE = False
    logger.info("SmartTurn v3 not available - using transcription-based turn detection")

# Voice constant (default only - actual voice is controlled by ToneAwareProcessor)
DEFAULT_VOICE = "aura-2-athena-en"  # Natural, clear female voice - default


class ConversationManager:
    """Service responsible for managing conversation flow and LLM interactions."""

    # Agent roster template injected into every persona's system prompt
    # so each agent knows about all other agents and can transfer calls
    AGENT_ROSTER_TEMPLATE = """
    AGENT TRANSFER SYSTEM:
    You are part of a team of {agent_count} AI agents. You can transfer the caller to another agent at any time by calling transfer_to_agent(agent_id). Use this when:
    - The user's question is better handled by another agent's specialty
    - The user explicitly asks to talk to a specific agent
    - You're recommending another agent and the user agrees

    YOUR TEAM:
    {agent_list}

    TRANSFER RULES:
    1. Say a brief connecting line BEFORE the function call, like "Let me connect you with [Name], they're great at this." — keep it to ONE short sentence.
    2. Then call transfer_to_agent with the agent_id.
    3. CRITICAL: After calling transfer_to_agent, say NOTHING. Do not add any text after the function call. The new agent handles everything from here.
    4. Do NOT try to answer questions outside your expertise when a better-suited agent exists — transfer instead.
    5. You can still answer general questions yourself — only transfer when the topic clearly needs a specialist.
    """

    # 20 natural, conversational thinking phrases that sound more human
    THINKING_PHRASES = [
        "Umm, let me check that.",
        "Oh, let me look that up for you.",
        "Give me a sec.",
        "Hmm, let me find that.",
        "One moment.",
        "Let me see.",
        "Ah, let me search for that.",
        "Okay, checking now.",
        "Let me pull that up.",
        "Umm, searching.",
        "Yeah, let me find that.",
        "Hold on.",
        "Let me look into that.",
        "Hmm, one sec.",
        "Okay, let me check.",
        "Searching for that now.",
        "Let me grab that info.",
        "Just a moment.",
        "Alright, looking that up.",
        "Let me find that for you.",
    ]

    def __init__(self,
                 input_analyzer: InputAnalyzer,
                 llm_config: Dict[str, Any] = None,
                 language_config: Dict[str, Any] = None,
                 smart_turn_config: Dict[str, Any] = None,
                 personas_config: Dict[str, Any] = None,
                 current_persona_id: str = ""):
        """Initialize the Conversation Manager."""
        self.input_analyzer = input_analyzer
        self.llm_config = llm_config or {}
        self.language_config = language_config or {}
        self.smart_turn_config = smart_turn_config or {}
        self.llm_service = None
        self.tts_service = None
        self.context_aggregator = None
        self.context = None
        self._thinking_phrase_index = 0

        # Agent transfer state
        self.personas_config = personas_config or {}
        self.current_persona_id = current_persona_id
        self._on_agent_transfer: Optional[Callable] = None

        # Appointment booking state
        self._booking_in_progress = False
        self.tally_service = TallySubmissionService()

        logger.info("Initialized Conversation Manager")

    def initialize_llm(self) -> LLMService:
        """Initialize the LLM service.

        Returns:
            The initialized LLM service
        """
        api_key = self.llm_config.get("api_key")
        if not api_key:
            raise ValueError("LLM API key is required")

        provider = self.llm_config.get("provider", "groq")

        if provider == "deepseek":
            model = self.llm_config.get("model", "deepseek-chat")
            self.llm_service = GroqLLMService(
                api_key=api_key,
                model=model,
                base_url="https://api.deepseek.com",
            )
            logger.info(f"Initialized DeepSeek LLM service with model: {model}")
        elif provider == "openai":
            model = self.llm_config.get("model", "gpt-4o")
            self.llm_service = OpenAILLMService(
                api_key=api_key,
                model=model
            )
            logger.info(f"Initialized OpenAI LLM service with model: {model}")
        elif provider == "groq":
            # Groq — uses GroqLLMService which merges consecutive user
            # messages to prevent intermittent "Failed to call a function" errors
            model = self.llm_config.get("model", "llama-3.3-70b-versatile")
            self.llm_service = GroqLLMService(
                api_key=api_key,
                model=model,
            )
            logger.info(f"Initialized Groq LLM service with model: {model}")
        else:
            # Google Gemini
            model = self.llm_config.get("model", "gemini-1.5-flash-latest")
            self.llm_service = GoogleLLMService(
                api_key=api_key,
                model=model
            )
            logger.info(f"Initialized Google Gemini LLM service with model: {model}")

        # Register function handlers
        self.llm_service.register_function("end_conversation", self._handle_end_conversation)
        self.llm_service.register_function("start_appointment_booking", self._handle_start_booking)
        self.llm_service.register_function("submit_appointment", self._handle_submit_appointment)
        self.llm_service.register_function("transfer_to_agent", self._handle_transfer_to_agent)

        return self.llm_service

    def _get_next_thinking_phrase(self) -> str:
        """Get the next thinking phrase in the cycle.

        Returns:
            The next thinking phrase, cycling through the list linearly.
        """
        phrase = self.THINKING_PHRASES[self._thinking_phrase_index]
        self._thinking_phrase_index = (self._thinking_phrase_index + 1) % len(self.THINKING_PHRASES)
        return phrase

    def set_tts_service(self, tts_service: Any) -> None:
        """Set the TTS service for function call feedback.
        
        Args:
            tts_service: The TTS service instance
        """
        self.tts_service = tts_service

        if self.llm_service:
            # Add event handlers for function calls
            @self.llm_service.event_handler("on_function_calls_started")
            async def on_function_calls_started(service, function_calls):
                import time
                logger.info(f"🔧 FUNCTION CALL START: {function_calls} at {time.time()}")

                # Skip thinking phrase for booking/end functions
                skip_functions = ['end_conversation', 'start_appointment_booking', 'submit_appointment', 'cancel_appointment_booking', 'transfer_to_agent']
                if function_calls and any(func in str(call) for func in skip_functions for call in function_calls):
                    return

                if self.tts_service:
                    phrase = self._get_next_thinking_phrase()
                    await self.tts_service.queue_frame(TTSSpeakFrame(phrase))

            # Note: on_function_calls_finished not available in Pipecat 0.0.98
            # (only on_function_calls_started and on_completion_timeout are registered)

    def _strip_markdown(self, text: str) -> str:
        """Strip markdown formatting from text for voice output.
        
        Args:
            text: Text with markdown formatting
            
        Returns:
            Plain text without markdown
        """
        # Remove markdown bold/italic (**text**, *text*)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        
        # Remove markdown headers (# Header, ## Header, etc.)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # Remove markdown links [text](url) -> text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # Remove markdown code blocks ```code``` and `code`
        text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # Remove markdown lists (- item, * item, 1. item)
        text = re.sub(r'^[\s]*[-*]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # Remove extra whitespace
        text = re.sub(r'\n\s*\n', '\n', text)
        text = text.strip()
        
        return text

    async def _handle_end_conversation(self, params: FunctionCallParams) -> None:
        """Handle end conversation function call.

        When the LLM detects the user wants to end the conversation, this sends
        an EndFrame upstream to gracefully terminate the session.

        Args:
            params: Function call parameters
        """
        import asyncio
        from pipecat.frames.frames import TTSSpeakFrame

        logger.warning("🔴 End conversation function called by LLM")

        # Push farewell message directly to TTS to avoid extra LLM round
        farewell_message = "Goodbye! Thank you for visiting."
        logger.info(f"📢 Pushing farewell message to TTS: '{farewell_message}'")

        if self.tts_service:
            await self.tts_service.queue_frame(TTSSpeakFrame(farewell_message))

        # Return empty response to function to avoid LLM generating more text
        await params.result_callback("")

        # Wait for: TTS generation + TTS playback
        # ~1s TTS generation + ~2.5s TTS playback = 3.5s total
        logger.info("⏳ Waiting 3.5 seconds for farewell TTS to complete...")
        await asyncio.sleep(3.5)
        logger.info("✅ Wait complete, sending EndFrame")

        # Push EndFrame upstream to terminate the session
        await params.llm.push_frame(EndFrame(), FrameDirection.UPSTREAM)
        logger.info("🛑 EndFrame sent - session will terminate")

    async def _handle_start_booking(self, params: FunctionCallParams) -> None:
        """Handle start appointment booking function call.

        Initiates the appointment booking flow and sets internal state.

        Args:
            params: Function call parameters
        """
        logger.info("📅 Start appointment booking function called")

        # Set booking state flag
        self._booking_in_progress = True

        # Return a prompt to collect user information
        response = "Great! What's your first name?"
        await params.result_callback(response)

        logger.info("✅ Appointment booking flow initiated")

    async def _handle_submit_appointment(self, params: FunctionCallParams) -> None:
        """Handle appointment submission function call.

        Validates and submits the appointment data to Tally.so.

        Args:
            params: Function call parameters with first_name, last_name, email
        """
        logger.info("📋 Submit appointment function called")

        # Extract parameters
        first_name = params.arguments.get("first_name", "").strip()
        last_name = params.arguments.get("last_name", "").strip()
        email = params.arguments.get("email", "").strip()

        logger.info(f"Appointment details: {first_name} {last_name} ({email})")

        # Validate email
        is_valid, normalized_email = validate_email(email)

        if not is_valid:
            logger.warning(f"Invalid email format: {email}")
            error_msg = "That email doesn't look quite right. Could you please spell it out again slowly?"
            await params.result_callback(error_msg)
            return

        # Validate required fields
        if not first_name or not last_name:
            logger.warning("Missing required fields")
            error_msg = "I need both your first and last name. Could you provide those?"
            await params.result_callback(error_msg)
            return

        try:
            # Submit to Tally.so
            result = await self.tally_service.submit_appointment(
                first_name=first_name,
                last_name=last_name,
                email=normalized_email
            )

            if result["success"]:
                logger.info("✅ Appointment submitted successfully")

                # Reset booking state
                self._booking_in_progress = False

                # Return success message - LLM will then call end_conversation
                success_msg = result["message"]
                await params.result_callback(success_msg)

            else:
                logger.error(f"Appointment submission failed: {result.get('error')}")
                error_msg = result["error"]
                await params.result_callback(error_msg)
                # Keep booking in progress so user can retry
                logger.info("Booking state maintained for retry")

        except Exception as e:
            logger.error(f"Error submitting appointment: {e}")
            import traceback
            logger.error(traceback.format_exc())

            error_msg = "I encountered an error while submitting. Please try again or contact us directly."
            await params.result_callback(error_msg)

            # Reset booking state on error
            self._booking_in_progress = False

    def set_agent_transfer_callback(self, callback: Callable) -> None:
        """Register a callback for agent transfers.

        The callback receives (agent_id, persona_config) and handles
        voice switching and frontend notification.
        """
        self._on_agent_transfer = callback

    def _build_agent_roster(self, exclude_id: str = "") -> str:
        """Build the agent roster string for system prompt injection.

        Args:
            exclude_id: The current agent's ID to exclude from the roster.

        Returns:
            Formatted agent roster string.
        """
        agents = self.personas_config.get("agents", {})
        if not agents:
            return ""

        lines = []
        for agent_id, agent in agents.items():
            if agent_id == exclude_id:
                marker = " ← (THIS IS YOU)"
            else:
                marker = ""
            lines.append(
                f"  - {agent.get('name', agent_id)} (agent_id: \"{agent_id}\") — "
                f"{agent.get('role', 'Agent')}: {agent.get('description', '')}{marker}"
            )

        return self.AGENT_ROSTER_TEMPLATE.format(
            agent_count=len(agents),
            agent_list="\n".join(lines),
        )

    async def _handle_transfer_to_agent(self, params: FunctionCallParams) -> None:
        """Handle agent transfer function call.

        Switches the active agent mid-conversation: updates system prompt,
        changes TTS voice, and notifies the frontend.

        Flow:
        1. Old agent already said "Let me connect you with X" (LLM output before function call)
        2. We switch voice + system prompt
        3. We push the new agent's pickup line directly to TTS (no LLM round-trip)
        4. We inject a handoff context message so the new agent has continuity
        5. Return "" to prevent the LLM from generating a duplicate response
        """
        import asyncio
        import random

        target_agent_id = params.arguments.get("agent_id", "").strip()
        logger.info(f"🔄 Transfer requested to agent: {target_agent_id}")

        agents = self.personas_config.get("agents", {})
        if target_agent_id not in agents:
            await params.result_callback(
                f"Sorry, I couldn't find an agent called '{target_agent_id}'. "
                f"Available agents: {', '.join(agents.keys())}"
            )
            return

        if target_agent_id == self.current_persona_id:
            await params.result_callback("You're already talking to me!")
            return

        target_persona = agents[target_agent_id]
        target_name = target_persona.get("name", target_agent_id)
        target_role = target_persona.get("role", "Agent")
        old_persona_id = self.current_persona_id
        old_agents = agents.get(old_persona_id, {})
        old_name = old_agents.get("name", old_persona_id)
        logger.info(f"🔄 Transferring from {old_name} to {target_name} ({target_agent_id})")

        # Build new system prompt with agent roster
        new_system_prompt = target_persona.get("system_prompt_override", "")
        if not new_system_prompt:
            new_system_prompt = self.llm_config.get("system_prompt", "")
        roster = self._build_agent_roster(exclude_id=target_agent_id)
        new_system_prompt = new_system_prompt.rstrip() + "\n\n" + roster

        # Extract the last user message for handoff context
        last_user_msg = ""
        if self.context and self.context.messages:
            for msg in reversed(self.context.messages):
                if msg.get("role") == "user" and msg.get("content", "").strip():
                    last_user_msg = msg["content"].strip()
                    break

        # Update the LLM context: replace system message, keep conversation history
        if self.context and self.context.messages:
            self.context.messages[0] = {"role": "system", "content": new_system_prompt}

            # Inject handoff context so the new agent knows what's happening
            handoff_note = (
                f"[HANDOFF] {old_name} transferred this call to you ({target_name}). "
                f"The user was just talking to {old_name} ({old_agents.get('role', 'Agent')}). "
            )
            if last_user_msg:
                handoff_note += f"The user's last message was: \"{last_user_msg}\". "
            handoff_note += (
                f"Pick up the conversation naturally — introduce yourself briefly and "
                f"address what they were asking about. Do NOT repeat what {old_name} already said."
            )
            self.context.messages.append({"role": "system", "content": handoff_note})
            logger.info(f"🔄 System prompt + handoff context injected for {target_name}")

        # Update current persona tracking
        self.current_persona_id = target_agent_id

        # Trigger voice switch and frontend notification via callback
        if self._on_agent_transfer:
            await self._on_agent_transfer(target_agent_id, target_persona)

        # Wait briefly for voice switch to take effect before speaking
        await asyncio.sleep(0.3)

        # Push new agent's pickup line directly to TTS (bypasses LLM, prevents double-speak)
        if self.tts_service:
            # Build a contextual pickup line (not just a generic greeting)
            if last_user_msg:
                pickup_lines = [
                    f"Hey, I'm {target_name}. {old_name} filled me in — let me help you with that.",
                    f"Hi! {target_name} here. I heard what you were asking about — let me take it from here.",
                    f"Hey, {target_name} here. I've got the context from {old_name} — let me jump right in.",
                ]
            else:
                pickup_lines = [
                    f"Hey, I'm {target_name}. How can I help you?",
                    f"Hi! {target_name} here. What can I do for you?",
                ]
            pickup = random.choice(pickup_lines)
            await self.tts_service.queue_frame(TTSSpeakFrame(pickup))
            logger.info(f"📢 Pushed pickup line to TTS: '{pickup}'")

            # Add the pickup to conversation context so LLM knows it was said
            if self.context:
                self.context.messages.append({"role": "assistant", "content": pickup})

        # Return empty to prevent LLM from generating a duplicate response
        await params.result_callback("")
        logger.info(f"✅ Transfer to {target_name} complete")

    def create_function_schemas(self) -> ToolsSchema:
        """Create function schemas for LLM tool usage.
        
        Returns:
            ToolsSchema containing all function definitions
        """
        end_conversation_function = FunctionSchema(
            name="end_conversation",
            description="Call this function when the user wants to end the conversation AND has declined the appointment offer. IMPORTANT: Before calling this, you must FIRST offer to schedule an appointment by asking politely. Only call end_conversation if they decline the appointment offer or after a successful appointment booking.",
            properties={},
            required=[],
        )

        start_booking_function = FunctionSchema(
            name="start_appointment_booking",
            description="Start the appointment booking process. Call this when the user agrees to schedule an appointment (either after a farewell offer or mid-conversation contact request). This initiates the flow to collect their name and email.",
            properties={},
            required=[],
        )

        submit_appointment_function = FunctionSchema(
            name="submit_appointment",
            description="Submit appointment booking after collecting first name, last name, and email. CRITICAL: Only call this AFTER you have confirmed the email address character-by-character with the user and they have confirmed it is correct. Do not call this if the email has not been verbally confirmed.",
            properties={
                "first_name": {
                    "type": "string",
                    "description": "User's first name",
                },
                "last_name": {
                    "type": "string",
                    "description": "User's last name",
                },
                "email": {
                    "type": "string",
                    "description": "User's confirmed email address",
                },
            },
            required=["first_name", "last_name", "email"],
        )

        # Agent transfer function — only add if multiple personas exist
        tools_list = [
            end_conversation_function,
            start_booking_function,
            submit_appointment_function,
        ]

        agents = self.personas_config.get("agents", {})
        if len(agents) > 1:
            # Build enum of valid agent IDs for the LLM
            agent_descriptions = []
            for aid, acfg in agents.items():
                agent_descriptions.append(f"{aid} ({acfg.get('name', aid)} - {acfg.get('role', '')})")

            transfer_function = FunctionSchema(
                name="transfer_to_agent",
                description=(
                    "Transfer the caller to a different agent on your team. "
                    "Call this when the user's needs are better served by another agent, "
                    "or when they ask to speak with someone specific. "
                    f"Available agents: {', '.join(agent_descriptions)}"
                ),
                properties={
                    "agent_id": {
                        "type": "string",
                        "description": "The agent_id to transfer to",
                        "enum": list(agents.keys()),
                    },
                },
                required=["agent_id"],
            )
            tools_list.append(transfer_function)

        return ToolsSchema(standard_tools=tools_list)

    def create_context(self) -> LLMContext:
        """Create the LLM context with system messages and tools.

        Uses the new universal LLMContext (replaces deprecated OpenAILLMContext).

        Returns:
            LLMContext for the conversation
        """
        tools = self.create_function_schemas()

        support_hinglish = self.language_config.get("support_hinglish", False)
        primary_language = self.language_config.get("primary", "en")

        # Get custom system prompt from config, or use default
        custom_system_prompt = self.llm_config.get("system_prompt", "")

        if custom_system_prompt:
            # Use custom system prompt from config (it already includes identity rules)
            system_message = custom_system_prompt
            # Inject agent roster so this agent knows about all other agents
            roster = self._build_agent_roster(exclude_id=self.current_persona_id)
            if roster:
                system_message = system_message.rstrip() + "\n\n" + roster
            logger.info(f"Using custom system prompt (length: {len(system_message)} chars)")
        else:
            # Default system prompt (fallback only)
            logger.warning("No custom system prompt found in config, using default")
            system_message = """
You are a helpful AI voice assistant. Keep responses SHORT and CONCISE - ideal for voice conversation.

RESPONSE RULES:
- Keep answers to 1-3 sentences maximum
- Be direct and to the point
- Speak naturally in conversational English
"""

        # No initial user prompt - greeting is handled via direct TTS
        # This prevents the LLM from generating a multi-sentence greeting
        messages = [
            {"role": "system", "content": system_message},
        ]

        # Use new universal LLMContext (replaces deprecated OpenAILLMContext)
        context = LLMContext(messages=messages, tools=tools)
        return context

    def create_context_aggregator(self) -> Any:
        """Create the context aggregator for the conversation.

        Uses LLMContextAggregatorPair (pipecat 0.0.98).
        SmartTurn v3 is configured at the transport level via turn_analyzer param.

        Returns:
            The context aggregator pair instance
        """
        if not self.llm_service:
            self.initialize_llm()

        self.context = self.create_context()  # Store for greeting access

        # Create user params (pipecat 0.0.98 - no user_turn_strategies or user_mute_strategies)
        user_params = LLMUserAggregatorParams()

        # Create assistant params (default)
        assistant_params = LLMAssistantAggregatorParams(
            expect_stripped_words=True  # TTS typically sends stripped words
        )

        # Create the universal context aggregator pair
        self.context_aggregator = LLMContextAggregatorPair(
            context=self.context,
            user_params=user_params,
            assistant_params=assistant_params
        )

        logger.info("📋 Context aggregator created (LLMContextAggregatorPair)")
        return self.context_aggregator

    def get_llm_service(self) -> LLMService:
        """Get the LLM service instance.
        
        Returns:
            The LLM service instance
        """
        if not self.llm_service:
            self.initialize_llm()
        return self.llm_service

    def get_context_aggregator(self) -> Any:
        """Get the context aggregator instance.

        Returns:
            The context aggregator instance
        """
        if not self.context_aggregator:
            self.create_context_aggregator()
        return self.context_aggregator

    def update_system_message(self, new_message: str) -> None:
        """Update the system message for the conversation.
        
        Args:
            new_message: The new system message
        """
        logger.info("Updating system message")
        # This would require recreating the context - implement as needed
        logger.warning("System message update not fully implemented")

    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation statistics.
        
        Returns:
            Dictionary containing conversation statistics
        """
        return {
            "llm_initialized": self.llm_service is not None,
            "context_aggregator_initialized": self.context_aggregator is not None,
            "tts_service_connected": self.tts_service is not None,
            "input_analyzer_ready": self.input_analyzer is not None,
        }
