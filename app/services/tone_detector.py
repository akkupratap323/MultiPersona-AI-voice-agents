"""Tone Detection service for dynamic voice selection.

This module detects the emotional tone of user input using Gemini Flash LLM
and maps it to appropriate TTS voice profiles for more natural conversation.
"""

import asyncio
import os
import time
from typing import Dict, Any, Optional, Tuple

from loguru import logger

# Emotion to Deepgram Aura-2 voice mapping
# All voices verified against Deepgram Aura-2 voice list (2025)
TONE_TO_VOICE = {
    # Primary tone mappings
    "neutral": "aura-2-athena-en",      # Calm, Smooth, Professional (default)
    "frustrated": "aura-2-neptune-en",  # Professional, Patient, Polite - calming for frustrated users
    "excited": "aura-2-thalia-en",      # Clear, Confident, Energetic, Enthusiastic - matches excitement
    "sad": "aura-2-vesta-en",           # Natural, Expressive, Patient, Empathetic - supportive for sad users
    # Extended emotion mappings
    "happy": "aura-2-thalia-en",        # Same as excited
    "angry": "aura-2-neptune-en",       # Same as frustrated
    "fear": "aura-2-luna-en",           # Gentle, calming
    "empathetic": "aura-asteria-en",    # Warm, supportive
}

# Default voice when tone detection fails
DEFAULT_VOICE = "aura-2-athena-en"

# Valid tones (core set used by SpeechBrain)
VALID_TONES = {"neutral", "frustrated", "excited", "sad", "happy", "angry", "fear", "empathetic"}


class ToneDetector:
    """Service for detecting emotional tone in user speech using Gemini Flash.

    Uses Google's Gemini Flash LLM for fast, accurate tone classification.
    Falls back to keyword-based detection if LLM fails.

    Attributes:
        last_tone: The last detected tone to prevent rapid switching
        tone_switch_cooldown: Minimum time between tone switches in seconds
        last_switch_time: Timestamp of last tone switch
    """

    # Fallback keywords for when LLM is unavailable
    FRUSTRATED_SIGNALS = [
        "not working", "doesn't work", "broken", "frustrat", "annoyed", "annoying",
        "angry", "upset", "problem", "issue", "wrong", "error", "failed", "failing",
        "can't", "won't", "terrible", "horrible", "awful", "hate", "stupid",
        "ridiculous", "unacceptable", "disappoint", "confus", "irritat", "mad"
    ]

    EXCITED_SIGNALS = [
        "amazing", "awesome", "fantastic", "great", "excellent", "wonderful",
        "love it", "excit", "wow", "incredible", "brilliant", "perfect",
        "can't wait", "thrill", "happy", "delight", "impress", "cool"
    ]

    SAD_SIGNALS = [
        "sad", "sorry", "unfortunately", "worried", "concerned", "anxious",
        "nervous", "scared", "afraid", "difficult", "struggling", "hard",
        "tough", "challenging", "help me", "don't understand", "lost"
    ]

    # Prompt for Gemini Flash tone detection
    TONE_DETECTION_PROMPT = """Analyze the emotional tone of this user message and respond with ONLY one word from: neutral, frustrated, excited, sad

Rules:
- "frustrated" = angry, annoyed, upset, complaining, having problems
- "excited" = happy, enthusiastic, impressed, amazed, delighted
- "sad" = worried, anxious, nervous, struggling, feeling down
- "neutral" = normal conversation, questions, greetings, factual statements

Examples:
"This is not working!" → frustrated
"Wow, that's amazing!" → excited
"I'm worried about this" → sad
"Can you tell me about your services?" → neutral
"Hello, how are you?" → neutral
"I'm so happy with this!" → excited
"This is frustrating" → frustrated

User message: "{text}"

Respond with ONLY one word (neutral/frustrated/excited/sad):"""

    def __init__(
        self,
        cooldown_seconds: float = 3.0,
        api_key: Optional[str] = None,
        use_llm: bool = True
    ):
        """Initialize the Tone Detector.

        Args:
            cooldown_seconds: Minimum time between tone switches to prevent chaos
            api_key: Google API key for Gemini. If None, uses GOOGLE_API_KEY env var
            use_llm: Whether to use LLM for detection (falls back to keywords if False)
        """
        self.last_tone = "neutral"
        self.tone_switch_cooldown = cooldown_seconds
        self.last_switch_time = 0.0
        self.use_llm = use_llm
        self._model = None
        self._api_key = api_key or os.environ.get("GOOGLE_API_KEY")

        # Initialize Gemini client
        if self.use_llm and self._api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self._api_key)
                self._model_name = "gemini-2.0-flash"
                self._model = True  # Flag that LLM is available
                logger.info("Initialized ToneDetector with Gemini Flash LLM (google.genai)")
            except ImportError:
                # Fallback to deprecated package
                try:
                    import google.generativeai as genai_old
                    genai_old.configure(api_key=self._api_key)
                    self._client = None
                    self._model = genai_old.GenerativeModel("gemini-2.0-flash")
                    logger.info("Initialized ToneDetector with Gemini Flash LLM (legacy)")
                except Exception as e:
                    logger.warning(f"Failed to initialize Gemini: {e}. Using keyword fallback.")
                    self._model = None
                    self._client = None
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {e}. Using keyword fallback.")
                self._model = None
                self._client = None
        else:
            logger.info("ToneDetector using keyword-based detection (LLM disabled or no API key)")
            self._client = None

        logger.info(f"ToneDetector initialized (cooldown={cooldown_seconds}s, llm={'enabled' if self._model else 'disabled'})")

    async def detect_tone_llm(self, text: str) -> str:
        """Detect emotional tone using Gemini Flash LLM.

        Args:
            text: User's transcribed speech

        Returns:
            Detected tone: "neutral", "frustrated", "excited", or "sad"
        """
        if not self._model:
            return self.detect_tone_keywords(text)

        try:
            start_time = time.time()
            prompt = self.TONE_DETECTION_PROMPT.format(text=text)

            loop = asyncio.get_event_loop()

            # Use new google.genai client if available, otherwise fall back to legacy
            if self._client:
                # New google.genai API
                from google.genai import types
                response = await loop.run_in_executor(
                    None,
                    lambda: self._client.models.generate_content(
                        model=self._model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.1,
                            max_output_tokens=10,
                        )
                    )
                )
                tone = response.text.strip().lower()
            else:
                # Legacy google.generativeai API
                response = await loop.run_in_executor(
                    None,
                    lambda: self._model.generate_content(
                        prompt,
                        generation_config={
                            "temperature": 0.1,
                            "max_output_tokens": 10,
                        }
                    )
                )
                tone = response.text.strip().lower()

            latency_ms = (time.time() - start_time) * 1000

            # Validate tone
            if tone in VALID_TONES:
                logger.debug(f"🎭 LLM tone detection: '{text[:50]}...' → {tone} ({latency_ms:.0f}ms)")
                return tone
            else:
                logger.warning(f"Invalid LLM tone response: '{tone}', falling back to keywords")
                return self.detect_tone_keywords(text)

        except Exception as e:
            logger.error(f"LLM tone detection failed: {e}, using keyword fallback")
            return self.detect_tone_keywords(text)

    def detect_tone_keywords(self, text: str) -> str:
        """Detect emotional tone using keyword matching (fallback).

        Args:
            text: User's transcribed speech

        Returns:
            Detected tone: "neutral", "frustrated", "excited", or "sad"
        """
        text_lower = text.lower()

        # Count signals for each tone
        frustrated_count = sum(1 for signal in self.FRUSTRATED_SIGNALS if signal in text_lower)
        excited_count = sum(1 for signal in self.EXCITED_SIGNALS if signal in text_lower)
        sad_count = sum(1 for signal in self.SAD_SIGNALS if signal in text_lower)

        # Determine dominant tone (need at least 1 signal)
        max_count = max(frustrated_count, excited_count, sad_count)

        if max_count == 0:
            return "neutral"
        elif frustrated_count == max_count:
            return "frustrated"
        elif excited_count == max_count:
            return "excited"
        elif sad_count == max_count:
            return "sad"

        return "neutral"

    def detect_tone(self, text: str) -> str:
        """Synchronous tone detection using keywords only.

        For async LLM detection, use detect_tone_llm() instead.

        Args:
            text: User's transcribed speech

        Returns:
            Detected tone: "neutral", "frustrated", "excited", or "sad"
        """
        return self.detect_tone_keywords(text)

    def should_switch_voice(self, new_tone: str) -> bool:
        """Check if voice should switch based on cooldown and tone change.

        Emotional tones (sad, frustrated, excited) are "sticky" - once in an
        emotional voice, the bot stays there until either:
        1. User expresses a DIFFERENT emotion (sad→excited, frustrated→sad, etc.)
        2. A long timeout passes (2 minutes)

        This prevents jarring voice changes when user says neutral things like
        "okay", "tell me more", "continue" while still in an emotional conversation.

        Args:
            new_tone: The newly detected tone

        Returns:
            True if voice should switch, False otherwise
        """
        current_time = time.time()

        logger.info(f"🔍 should_switch_voice: new={new_tone}, last={self.last_tone}, last_switch_time={self.last_switch_time}")

        # Don't switch if same tone
        if new_tone == self.last_tone:
            logger.debug(f"Same tone, no switch: {new_tone}")
            return False

        # Allow first switch immediately (last_switch_time is 0 at start)
        # This ensures the first emotional detection switches the voice right away
        if self.last_switch_time == 0.0:
            logger.info(f"✅ First voice switch allowed immediately: {self.last_tone} → {new_tone}")
            return True

        # Standard cooldown for subsequent switches
        time_since_switch = current_time - self.last_switch_time
        if time_since_switch < self.tone_switch_cooldown:
            logger.debug(f"Tone switch blocked by cooldown: {time_since_switch:.1f}s < {self.tone_switch_cooldown}s ({self.last_tone} → {new_tone})")
            return False

        # STICKY EMOTIONAL TONES: Once in an emotional voice, NEVER switch to neutral
        # Only switch if user expresses a DIFFERENT emotion, or after a very long timeout
        emotional_tones = {"sad", "frustrated", "excited"}
        if self.last_tone in emotional_tones and new_tone == "neutral":
            # Very long timeout (2 minutes) before allowing neutral switch
            sticky_timeout = 120.0  # 2 minutes
            if current_time - self.last_switch_time < sticky_timeout:
                logger.debug(
                    f"Staying in {self.last_tone} voice (ignoring neutral detection, "
                    f"{sticky_timeout - (current_time - self.last_switch_time):.0f}s until timeout)"
                )
                return False
            else:
                logger.info(f"Sticky timeout reached, allowing switch to neutral")

        logger.info(f"✅ Voice switch ALLOWED: {self.last_tone} → {new_tone}")
        return True

    def get_voice_for_tone(self, tone: str) -> str:
        """Get the appropriate voice for a given tone.

        Args:
            tone: The detected emotional tone

        Returns:
            Deepgram Aura-2 voice model name
        """
        return TONE_TO_VOICE.get(tone, DEFAULT_VOICE)

    async def process_input_async(self, text: str) -> Tuple[str, str, bool]:
        """Process user input asynchronously using LLM tone detection.

        Args:
            text: User's transcribed speech

        Returns:
            Tuple of (detected_tone, voice_model, should_switch)
        """
        detected_tone = await self.detect_tone_llm(text)
        voice = self.get_voice_for_tone(detected_tone)
        should_switch = self.should_switch_voice(detected_tone)

        if should_switch:
            logger.info(f"🎭 TONE CHANGE: {self.last_tone} → {detected_tone} | Voice: {voice}")
            self.last_tone = detected_tone
            self.last_switch_time = time.time()
        else:
            logger.debug(f"Tone: {detected_tone} (keeping voice: {self.get_voice_for_tone(self.last_tone)})")

        return detected_tone, voice, should_switch

    def process_input(self, text: str) -> Tuple[str, str, bool]:
        """Process user input synchronously (keyword-based fallback).

        For LLM-based detection, use process_input_async() instead.

        Args:
            text: User's transcribed speech

        Returns:
            Tuple of (detected_tone, voice_model, should_switch)
        """
        detected_tone = self.detect_tone_keywords(text)
        voice = self.get_voice_for_tone(detected_tone)
        should_switch = self.should_switch_voice(detected_tone)

        if should_switch:
            logger.info(f"🎭 TONE CHANGE: {self.last_tone} → {detected_tone} | Voice: {voice}")
            self.last_tone = detected_tone
            self.last_switch_time = time.time()
        else:
            logger.debug(f"Tone: {detected_tone} (keeping voice: {self.get_voice_for_tone(self.last_tone)})")

        return detected_tone, voice, should_switch

    def get_current_voice(self) -> str:
        """Get the current voice based on last tone.

        Returns:
            Current Deepgram Aura-2 voice model name
        """
        return self.get_voice_for_tone(self.last_tone)

    def reset(self) -> None:
        """Reset tone detector to default state."""
        self.last_tone = "neutral"
        self.last_switch_time = 0.0
        logger.info("ToneDetector reset to neutral")

    def get_stats(self) -> Dict[str, Any]:
        """Get tone detector statistics.

        Returns:
            Dictionary with current state info
        """
        return {
            "last_tone": self.last_tone,
            "current_voice": self.get_current_voice(),
            "cooldown_seconds": self.tone_switch_cooldown,
            "time_since_switch": time.time() - self.last_switch_time if self.last_switch_time > 0 else None,
            "llm_enabled": self._model is not None,
        }
