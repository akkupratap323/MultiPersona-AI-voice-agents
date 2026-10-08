"""
Tests for text-sentiment failure handling in the hybrid emotion detector.

A failed or missing text judgement must not be fused as a confident "neutral":
that pulls every emotion 30% toward the middle (e.g. angry -> anxious).
"""

import asyncio

import httpx
import pytest

from app.services.hybrid_emotion_detector import HybridEmotionDetector
from app.services.llm_text_sentiment import DEFAULT_MODEL, LLMTextSentiment

# Audio result measured on an EARS anger clip (p001) by the MSP-PODCAST model.
ANGRY_AUDIO = {"emotion": "angry", "arousal": 0.73, "valence": 0.26, "dominance": 0.75, "confidence": 0.47}


def make_llm(handler):
    detector = LLMTextSentiment(api_key="gsk_test", model="test-model")
    detector._client = httpx.Client(transport=httpx.MockTransport(handler))
    return detector


def reply(content):
    return lambda request: httpx.Response(
        200, json={"choices": [{"message": {"content": content}}], "usage": {"total_tokens": 7}}
    )


def run_hybrid(llm, transcript="I'm so mad right now"):
    hybrid = HybridEmotionDetector(audio_detector=None, llm_api_key=None)
    hybrid.llm_detector = llm
    return asyncio.run(hybrid.detect_hybrid_emotion(audio_emotion_result=ANGRY_AUDIO, transcript=transcript))


class TestLLMTextSentiment:
    def test_success_is_available(self):
        result = make_llm(reply("frustrated")).detect_emotion("This is really annoying!")
        assert result["emotion"] == "frustrated"
        assert result["available"] is True

    def test_api_error_is_unavailable_not_confident_neutral(self):
        result = make_llm(lambda request: httpx.Response(404, json={"error": "model_not_found"})).detect_emotion("hi")
        assert result["available"] is False
        assert result["confidence"] == 0.0
        assert result["reason"].startswith("Error")

    def test_empty_text_is_unavailable(self):
        result = make_llm(reply("neutral")).detect_emotion("   ")
        assert result["available"] is False

    def test_default_model_and_env_override(self, monkeypatch):
        monkeypatch.delenv("GROQ_SENTIMENT_MODEL", raising=False)
        assert LLMTextSentiment(api_key="gsk_test").model == DEFAULT_MODEL
        monkeypatch.setenv("GROQ_SENTIMENT_MODEL", "other/model")
        assert LLMTextSentiment(api_key="gsk_test").model == "other/model"
        assert LLMTextSentiment(api_key="gsk_test", model="explicit").model == "explicit"


class TestHybridFallback:
    def test_failed_text_uses_audio_alone(self):
        result = run_hybrid(make_llm(lambda request: httpx.Response(401)))
        assert result["text_available"] is False
        assert result["weights"] == {"audio": 1.0, "text": 0.0}
        # Previously fused with neutral -> valence 0.33 -> "anxious".
        assert result["primary_emotion"] == "angry"

    def test_no_llm_detector_uses_audio_alone(self):
        result = run_hybrid(None)
        assert result["text_available"] is False
        assert result["primary_emotion"] == "angry"

    def test_working_text_is_fused(self):
        result = run_hybrid(make_llm(reply("frustrated")))
        assert result["text_available"] is True
        assert result["weights"] == {"audio": pytest.approx(0.7), "text": pytest.approx(0.3)}
        assert result["primary_emotion"] == "angry"
        assert result["valence"] == pytest.approx(0.7 * 0.26 + 0.3 * 0.25)
