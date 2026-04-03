"""
LLM-based text sentiment detector using Groq.

This module provides contextual emotion detection from text using an LLM
via the Groq OpenAI-compatible API.

Classes: frustrated, excited, sad, neutral
Latency: ~50-150ms (Groq is optimised for low-latency inference)
"""

import os
from typing import Dict, Optional
from loguru import logger
import httpx


class LLMTextSentiment:
    """Contextual text sentiment detector using Groq."""

    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

    # Map LLM emotions to our 4 core emotions with dimensional scores
    EMOTION_DIMENSIONS = {
        "frustrated": {"arousal": 0.75, "valence": 0.25},
        "excited": {"arousal": 0.80, "valence": 0.80},
        "sad": {"arousal": 0.30, "valence": 0.30},
        "neutral": {"arousal": 0.50, "valence": 0.50}
    }

    PROMPT = (
        "You are an emotion detection expert. Analyze the emotional tone of the user message.\n"
        "Respond with ONLY ONE WORD from these options: frustrated, excited, sad, neutral\n\n"
        "Examples:\n"
        '- "This is really annoying!" → frustrated\n'
        '- "I love this so much!" → excited\n'
        '- "I\'m feeling down today" → sad\n'
        '- "Okay, thanks" → neutral\n\n'
        "Analyze the emotion in this text: \"{text}\"\n\n"
        "Your response (one word only):"
    )

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.1-8b-instant",
    ):
        """Initialize the LLM sentiment detector.

        Args:
            api_key: Groq API key
            model: Groq model name
        """
        self.api_key = api_key
        self.model = model
        self._client = httpx.Client(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=5.0,
        )
        logger.info(f"LLM Text Sentiment initialized (model: {model}, provider: Groq)")

    def detect_emotion(self, text: str) -> Dict:
        """Detect emotion from text using Groq LLM.

        Args:
            text: Input text to analyze

        Returns:
            Dictionary with emotion, confidence, arousal, valence, etc.
        """
        if not text or not text.strip():
            return self._neutral_result("Empty text")

        try:
            resp = self._client.post(
                self.GROQ_URL,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": self.PROMPT.format(text=text)}
                    ],
                    "max_tokens": 5,
                    "temperature": 0.1,
                },
            )
            resp.raise_for_status()

            raw_response = resp.json()["choices"][0]["message"]["content"].strip().lower()
            tokens_used = resp.json().get("usage", {}).get("total_tokens", 0)

            # Parse emotion — first match wins
            detected_emotion = "neutral"
            for emotion in ["frustrated", "excited", "sad", "neutral"]:
                if emotion in raw_response:
                    detected_emotion = emotion
                    break

            dimensions = self.EMOTION_DIMENSIONS[detected_emotion]
            confidence = 0.85 if detected_emotion in raw_response else 0.60

            logger.debug(
                f"LLM sentiment: '{text[:50]}...' → {detected_emotion} "
                f"(tokens: {tokens_used}, conf: {confidence:.2f})"
            )

            return {
                "emotion": detected_emotion,
                "raw_emotion": detected_emotion,
                "confidence": confidence,
                "arousal": dimensions["arousal"],
                "valence": dimensions["valence"],
                "dominance": 0.5,
                "raw_response": raw_response,
                "method": "llm",
                "tokens_used": tokens_used,
                "latency_ms": 0,
            }

        except Exception as e:
            logger.error(f"LLM emotion detection failed: {e}")
            return self._neutral_result(f"Error: {str(e)}")

    def _neutral_result(self, reason: str) -> Dict:
        """Return neutral emotion result."""
        return {
            "emotion": "neutral",
            "raw_emotion": "neutral",
            "confidence": 1.0,
            "arousal": 0.5,
            "valence": 0.5,
            "dominance": 0.5,
            "raw_response": "neutral",
            "method": "llm_fallback",
            "tokens_used": 0,
            "reason": reason
        }

    def batch_detect(self, texts: list[str]) -> list[Dict]:
        """Detect emotions for multiple texts (sequential calls for now).

        Args:
            texts: List of text strings to analyze

        Returns:
            List of emotion dictionaries
        """
        results = []
        for text in texts:
            results.append(self.detect_emotion(text))
        return results

    def get_status(self) -> Dict:
        """Get detector status."""
        return {
            "model": self.model,
            "provider": "groq",
            "available": self._client is not None,
            "tokens_per_detection": "~20-50"
        }


# Global instance for reuse
_llm_detector: Optional[LLMTextSentiment] = None


def get_llm_detector(api_key: str = None) -> LLMTextSentiment:
    """Get or create global LLM detector instance.

    Args:
        api_key: Groq API key. Falls back to GROQ_API_KEY env var.
    """
    global _llm_detector
    if _llm_detector is None:
        key = api_key or os.getenv("GROQ_API_KEY")
        if not key:
            raise ValueError("GROQ_API_KEY env var required to initialize LLM detector")
        _llm_detector = LLMTextSentiment(api_key=key)
    return _llm_detector
