"""
Hybrid Emotion Detector - Combines Audio + Text Sentiment Analysis.

This module implements a sophisticated emotion detection system that fuses:
1. Audio emotion from MSP-PODCAST wav2vec2 (70% weight)
2. Text sentiment from Google Gemini LLM (30% weight)

Features:
- Dynamic weight adjustment based on confidence scores
- Emotion mismatch detection (sarcasm, politeness masking)
- Dimensional emotion fusion (arousal, valence, dominance)
- Fast LLM inference via Google Gemini Flash
"""

import math
from typing import Dict, Optional, Tuple
from loguru import logger

from app.services.llm_text_sentiment import get_llm_detector


class HybridEmotionDetector:
    """Combines audio and text emotion detection for robust sentiment analysis."""

    def __init__(
        self,
        audio_detector=None,
        llm_api_key: str = None,
        default_audio_weight: float = 0.7,
        default_text_weight: float = 0.3,
        min_confidence: float = 0.25,
        mismatch_threshold: float = 0.8
    ):
        """Initialize hybrid emotion detector.

        Args:
            audio_detector: Audio emotion detector (MSP or SpeechBrain)
            llm_api_key: Google AI API key for Gemini text sentiment
            default_audio_weight: Default weight for audio emotion (0-1)
            default_text_weight: Default weight for text sentiment (0-1)
            min_confidence: Minimum confidence threshold
            mismatch_threshold: Threshold for detecting emotion mismatch
        """
        self.audio_detector = audio_detector
        logger.info(
            f"[EMOTION-DIAG] HybridEmotionDetector init: "
            f"llm_api_key={'SET' if llm_api_key else 'NONE'}, "
            f"audio_detector={audio_detector is not None}"
        )
        try:
            self.llm_detector = get_llm_detector(api_key=llm_api_key) if llm_api_key else None
        except Exception as e:
            logger.error(f"[EMOTION-DIAG] Failed to init LLM detector: {e}")
            self.llm_detector = None

        # Configurable weights
        self.default_audio_weight = default_audio_weight
        self.default_text_weight = default_text_weight
        self.min_confidence = min_confidence
        self.mismatch_threshold = mismatch_threshold

        logger.info(
            f"[EMOTION-DIAG] Hybrid Emotion Detector initialized: "
            f"audio_weight={default_audio_weight}, text_weight={default_text_weight}, "
            f"mismatch_threshold={mismatch_threshold}, "
            f"llm_detector={'READY' if self.llm_detector else 'NONE (text sentiment disabled)'}"
        )

    async def detect_hybrid_emotion(
        self,
        audio_chunk: Optional[bytes] = None,
        transcript: str = "",
        audio_emotion_result: Optional[Dict] = None
    ) -> Dict:
        """Detect emotion using both audio and text.

        Args:
            audio_chunk: Raw audio bytes (optional if audio_emotion_result provided)
            transcript: Transcribed text from speech
            audio_emotion_result: Pre-computed audio emotion (optional)

        Returns:
            Dictionary containing:
                - primary_emotion: Main detected emotion
                - secondary_emotion: Secondary emotion if mismatch detected
                - arousal: Fused arousal score (0-1)
                - valence: Fused valence score (0-1)
                - dominance: Fused dominance score (0-1)
                - audio_confidence: Audio detection confidence
                - text_confidence: Text detection confidence
                - weights: Applied weights {audio, text}
                - mismatch_detected: Boolean flag
                - interpretation: Human-readable interpretation
                - components: Breakdown of audio and text results
                - tokens_used: 0 (no LLM)
        """
        # Get audio emotion
        audio_result = audio_emotion_result
        if audio_result is None and audio_chunk and self.audio_detector:
            try:
                audio_result = await self.audio_detector.detect_emotion(audio_chunk)
            except Exception as e:
                logger.warning(f"Audio emotion detection failed: {e}")
                audio_result = self._neutral_audio_result()
        elif audio_result is None:
            audio_result = self._neutral_audio_result()

        # Get text sentiment (LLM - contextual understanding!)
        if transcript and transcript.strip() and transcript != "...":
            logger.debug(f"📝 Calling LLM for text sentiment: '{transcript[:100]}'")
            text_result = self.llm_detector.detect_emotion(transcript) if self.llm_detector else self._neutral_text_result()
            logger.debug(f"📝 LLM result: {text_result['emotion']} (conf: {text_result['confidence']:.2f}, tokens: {text_result.get('tokens_used', 0)})")
        else:
            logger.debug(f"📝 Empty/invalid transcript, using neutral: '{transcript}'")
            text_result = self._neutral_text_result()

        # Calculate dynamic weights based on confidence
        audio_weight, text_weight = self._calculate_dynamic_weights(
            audio_result.get("confidence", 0.5),
            text_result.get("confidence", 0.5)
        )

        # Fuse dimensional scores (arousal, valence, dominance)
        fused_scores = self._fuse_scores(
            audio_result,
            text_result,
            audio_weight,
            text_weight
        )

        # Map to categorical emotion
        primary_emotion = self._map_to_category(
            fused_scores["arousal"],
            fused_scores["valence"],
            fused_scores["dominance"]
        )

        # Detect mismatch between audio and text
        mismatch_info = self._detect_mismatch(
            audio_result.get("emotion", "neutral"),
            text_result.get("emotion", "neutral"),
            audio_result.get("confidence", 0.5),
            text_result.get("confidence", 0.5)
        )

        # Calculate overall confidence
        overall_confidence = (
            audio_result.get("confidence", 0.5) * audio_weight +
            text_result.get("confidence", 0.5) * text_weight
        )

        logger.info(
            f"Hybrid emotion: {primary_emotion} "
            f"(audio={audio_result.get('emotion')}/{audio_result.get('confidence', 0):.2f}, "
            f"text={text_result.get('emotion')}/{text_result.get('confidence', 0):.2f}, "
            f"weights={audio_weight:.0%}/{text_weight:.0%}, "
            f"mismatch={mismatch_info['has_mismatch']})"
        )

        return {
            # Primary results
            "primary_emotion": primary_emotion,
            "secondary_emotion": mismatch_info.get("secondary_emotion"),

            # Dimensional scores (fused)
            "arousal": fused_scores["arousal"],
            "valence": fused_scores["valence"],
            "dominance": fused_scores["dominance"],

            # Confidence scores
            "audio_confidence": audio_result.get("confidence", 0.5),
            "text_confidence": text_result.get("confidence", 0.5),
            "overall_confidence": overall_confidence,

            # Weight information
            "weights": {
                "audio": audio_weight,
                "text": text_weight
            },

            # Sentiment contribution percentages (for UI)
            "sentiment_contribution": {
                "audio_percentage": int(audio_weight * 100),
                "text_percentage": int(text_weight * 100)
            },

            # Mismatch detection
            "mismatch_detected": mismatch_info["has_mismatch"],
            "mismatch_score": mismatch_info.get("mismatch_score", 0.0),
            "interpretation": mismatch_info.get("interpretation", ""),

            # Component breakdown
            "components": {
                "audio": {
                    "emotion": audio_result.get("emotion", "neutral"),
                    "arousal": audio_result.get("arousal", 0.5),
                    "valence": audio_result.get("valence", 0.5),
                    "dominance": audio_result.get("dominance", 0.5),
                    "confidence": audio_result.get("confidence", 0.5),
                    "weight_applied": audio_weight
                },
                "text": {
                    "emotion": text_result.get("emotion", "neutral"),
                    "raw_emotion": text_result.get("raw_emotion", "neutral"),
                    "raw_response": text_result.get("raw_response", "neutral"),
                    "arousal": text_result.get("arousal", 0.5),
                    "valence": text_result.get("valence", 0.5),
                    "confidence": text_result.get("confidence", 0.5),
                    "weight_applied": text_weight
                }
            },

            # Token usage
            "tokens_used": text_result.get("tokens_used", 0),  # LLM tokens used for text sentiment
            "method": "hybrid_audio_llm"
        }

    def _calculate_dynamic_weights(
        self,
        audio_conf: float,
        text_conf: float
    ) -> Tuple[float, float]:
        """Calculate dynamic weights based on confidence scores.

        Args:
            audio_conf: Audio confidence (0-1)
            text_conf: Text confidence (0-1)

        Returns:
            Tuple of (audio_weight, text_weight)
        """
        # ALWAYS use default weights (70% audio, 30% text)
        # Confidence-based adjustment is DISABLED per user requirement
        audio_weight = self.default_audio_weight  # 0.7
        text_weight = self.default_text_weight    # 0.3

        logger.debug(f"Using fixed weights: audio={audio_weight:.0%}, text={text_weight:.0%}")

        return audio_weight, text_weight

    def _fuse_scores(
        self,
        audio_result: Dict,
        text_result: Dict,
        audio_weight: float,
        text_weight: float
    ) -> Dict:
        """Fuse dimensional scores using weighted average.

        Args:
            audio_result: Audio emotion result
            text_result: Text sentiment result
            audio_weight: Weight for audio
            text_weight: Weight for text

        Returns:
            Dictionary with fused arousal, valence, dominance
        """
        return {
            "arousal": (
                audio_result.get("arousal", 0.5) * audio_weight +
                text_result.get("arousal", 0.5) * text_weight
            ),
            "valence": (
                audio_result.get("valence", 0.5) * audio_weight +
                text_result.get("valence", 0.5) * text_weight
            ),
            "dominance": (
                audio_result.get("dominance", 0.5) * audio_weight +
                text_result.get("dominance", 0.5) * text_weight
            )
        }

    def _map_to_category(
        self,
        arousal: float,
        valence: float,
        dominance: float
    ) -> str:
        """Map dimensional scores to categorical emotion.

        Maps to granular Cartesia-compatible emotions so the emotion map in
        tone_aware_processor.py can apply fine-grained voice control.

        Args:
            arousal: Energy level (0-1)
            valence: Positive/negative (0-1)
            dominance: Control/confidence (0-1)

        Returns:
            Categorical emotion string matching CARTESIA_EMOTION_CONFIG keys
        """
        # High arousal (> 0.6) — energetic states
        if arousal > 0.6:
            if valence < 0.3:
                if dominance > 0.65:
                    return "angry"        # High energy + very negative + dominant
                return "frustrated"       # High energy + negative + not dominant
            elif valence < 0.45:
                return "anxious"          # High energy + slightly negative = tense
            elif valence > 0.7:
                return "excited"          # High energy + very positive (→ enthusiastic in Cartesia)
            elif valence > 0.55:
                return "happy"            # High energy + moderately positive
            else:
                return "confident"        # High energy + neutral valence = assertive

        # Medium arousal (0.4–0.6)
        elif arousal > 0.4:
            if valence < 0.3:
                return "sad"              # Medium energy + negative
            elif valence < 0.45:
                return "disappointed"     # Medium energy + mildly negative
            elif valence > 0.65:
                return "happy"            # Medium energy + positive
            elif valence > 0.5:
                return "content"          # Medium energy + slightly positive = settled
            else:
                return "neutral"

        # Low arousal (< 0.4) — subdued states
        else:
            if valence < 0.25:
                if dominance < 0.35:
                    return "fear"         # Low energy + very negative + submissive (→ scared)
                return "sad"              # Low energy + negative
            elif valence < 0.4:
                return "apologetic"       # Low energy + mildly negative = subdued/sorry
            elif valence > 0.6:
                return "content"          # Low energy + positive = calm/relaxed
            elif valence > 0.45:
                return "empathetic"       # Low energy + slightly positive = warm/gentle
            else:
                return "neutral"

    def _detect_mismatch(
        self,
        audio_emotion: str,
        text_emotion: str,
        audio_conf: float,
        text_conf: float
    ) -> Dict:
        """Detect when audio and text emotions diverge.

        Args:
            audio_emotion: Emotion from audio
            text_emotion: Emotion from text
            audio_conf: Audio confidence
            text_conf: Text confidence

        Returns:
            Dictionary with mismatch information
        """
        # Emotion coordinate mapping for distance calculation
        emotion_coords = {
            "frustrated": {"arousal": 0.8, "valence": 0.2},
            "excited": {"arousal": 0.8, "valence": 0.8},
            "sad": {"arousal": 0.3, "valence": 0.2},
            "neutral": {"arousal": 0.5, "valence": 0.5}
        }

        audio_vec = emotion_coords.get(audio_emotion, emotion_coords["neutral"])
        text_vec = emotion_coords.get(text_emotion, emotion_coords["neutral"])

        # Calculate Euclidean distance
        distance = math.sqrt(
            (audio_vec["arousal"] - text_vec["arousal"]) ** 2 +
            (audio_vec["valence"] - text_vec["valence"]) ** 2
        )

        # Only flag mismatch if both are confident
        has_mismatch = (
            distance > self.mismatch_threshold and
            audio_conf > 0.6 and
            text_conf > 0.6
        )

        if has_mismatch:
            interpretation = self._interpret_mismatch(audio_emotion, text_emotion)
            logger.info(f"Emotion mismatch detected: {interpretation}")
            return {
                "has_mismatch": True,
                "secondary_emotion": text_emotion,
                "mismatch_score": distance,
                "interpretation": interpretation
            }

        return {"has_mismatch": False}

    def _interpret_mismatch(self, audio_emotion: str, text_emotion: str) -> str:
        """Provide human-readable interpretation of emotion mismatch."""
        patterns = {
            ("frustrated", "neutral"): "User masking frustration with polite language",
            ("frustrated", "excited"): "User expressing frustration with positive words (sarcasm possible)",
            ("frustrated", "sad"): "User frustrated but expressing sadness verbally",
            ("excited", "neutral"): "User enthusiastic but using formal/brief language",
            ("excited", "frustrated"): "User excited vocally but text shows concern",
            ("excited", "sad"): "User trying to stay positive despite sadness",
            ("sad", "neutral"): "User hiding sadness, maintaining professional tone",
            ("sad", "excited"): "User masking sadness with positive words",
            ("sad", "frustrated"): "User sad but expressing frustration",
            ("neutral", "frustrated"): "User expressing frustration verbally but voice calm",
            ("neutral", "excited"): "User excited in text but voice controlled",
            ("neutral", "sad"): "User expressing sadness in text but voice controlled"
        }

        return patterns.get(
            (audio_emotion, text_emotion),
            f"Emotion mismatch: voice={audio_emotion}, text={text_emotion}"
        )

    def _neutral_audio_result(self) -> Dict:
        """Return neutral audio emotion result."""
        return {
            "emotion": "neutral",
            "arousal": 0.5,
            "valence": 0.5,
            "dominance": 0.5,
            "confidence": 0.5
        }

    def _neutral_text_result(self) -> Dict:
        """Return neutral text sentiment result."""
        return {
            "emotion": "neutral",
            "arousal": 0.5,
            "valence": 0.5,
            "dominance": 0.5,
            "confidence": 0.5
        }

    def get_status(self) -> Dict:
        """Get detector status."""
        return {
            "type": "hybrid_audio_llm",
            "audio_weight": self.default_audio_weight,
            "text_weight": self.default_text_weight,
            "mismatch_threshold": self.mismatch_threshold,
            "llm_status": self.llm_detector.get_status() if self.llm_detector else None,
            "tokens_per_detection": "~20-50 (text only)"
        }


# Global instance
_hybrid_detector: Optional[HybridEmotionDetector] = None


def get_hybrid_detector(audio_detector=None, llm_api_key: str = None) -> HybridEmotionDetector:
    """Get or create global hybrid detector instance."""
    global _hybrid_detector
    if _hybrid_detector is None:
        _hybrid_detector = HybridEmotionDetector(audio_detector=audio_detector, llm_api_key=llm_api_key)
    return _hybrid_detector
