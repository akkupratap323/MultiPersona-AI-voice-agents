"""
Unit tests for the InputAnalyzer service.
"""

import pytest
from app.services.input_analyzer import InputAnalyzer


class TestInputAnalyzer:
    """Test cases for InputAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create InputAnalyzer instance."""
        return InputAnalyzer()

    def test_greeting_detection(self, analyzer):
        """Test that greetings are correctly detected."""
        greetings = [
            "Hello",
            "Hi there",
            "Hey",
            "Good morning",
            "Good afternoon",
            "Good evening",
            "What's up",
        ]

        for greeting in greetings:
            assert analyzer.is_greeting_or_feedback(greeting) is True

    def test_feedback_detection(self, analyzer):
        """Test that feedback phrases are correctly detected."""
        feedback_phrases = [
            "Thank you",
            "Thanks",
            "That was helpful",
            "Great response",
            "I appreciate it",
        ]

        for phrase in feedback_phrases:
            assert analyzer.is_greeting_or_feedback(phrase) is True

    def test_ending_detection(self, analyzer):
        """Test that conversation ending phrases are correctly detected."""
        ending_phrases = [
            "Goodbye",
            "Bye",
            "See you",
            "Talk to you later",
            "End the conversation",
        ]

        for phrase in ending_phrases:
            assert analyzer.is_conversation_ending(phrase) is True

    def test_question_detection(self, analyzer):
        """Test that questions are not detected as greetings/feedback."""
        questions = [
            "What is the capital of France?",
            "How does the RAG system work?",
            "Tell me about Nester Labs",
            "What services do you offer?",
        ]

        for question in questions:
            assert analyzer.is_greeting_or_feedback(question) is False

    def test_analyze_input_normal_conversation(self, analyzer):
        """Test analyze_input returns normal_conversation for greetings."""
        result = analyzer.analyze_input("Hello, how are you?")
        assert result == "normal_conversation"

    def test_analyze_input_needs_rag(self, analyzer):
        """Test analyze_input returns needs_rag for questions."""
        result = analyzer.analyze_input("What are Nester Labs services?")
        assert result == "needs_rag"

    def test_custom_patterns(self):
        """Test adding custom patterns."""
        custom_patterns = {
            "greeting": [r"\bnamaste\b"],
            "feedback": [r"\bdhanyavaad\b"],
        }
        analyzer = InputAnalyzer(custom_patterns=custom_patterns)

        assert analyzer.is_greeting_or_feedback("Namaste") is True

    def test_case_insensitivity(self, analyzer):
        """Test that detection is case insensitive."""
        assert analyzer.is_greeting_or_feedback("HELLO") is True
        assert analyzer.is_greeting_or_feedback("hello") is True
        assert analyzer.is_greeting_or_feedback("HeLLo") is True

    def test_get_input_type_details(self, analyzer):
        """Test detailed analysis output."""
        result = analyzer.get_input_type_details("Hello there!")

        assert "input" in result
        assert "type" in result
        assert "matched_patterns" in result
        assert "confidence" in result
        assert result["type"] == "normal_conversation"
