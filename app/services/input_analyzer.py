"""Input Analyzer service for the Voice RAG Assistant.

This module handles analyzing user input to determine the appropriate processing type.
"""

import re
from typing import Literal, Dict, List, Any

from loguru import logger


class InputAnalyzer:
    """Service responsible for analyzing user input and determining processing type.
    
    This class determines whether user input should be handled as normal conversation
    or needs RAG processing based on input patterns.
    """

    def __init__(self, custom_patterns: Dict[str, List[str]] = None):
        """Initialize the Input Analyzer.
        
        Args:
            custom_patterns: Custom patterns for different input types
        """
        self.greeting_patterns = [
            r'\b(hi|hello|hey|good morning|good afternoon|good evening)\b',
            r'\bhow are you\b',
            r'\bnice to meet you\b',
            r'\bwhat\'s up\b',
            r'\bwhats up\b'
        ]

        self.feedback_patterns = [
            r'\b(thank you|thanks|appreciate|good job|well done|excellent)\b',
            r'\bthat was helpful\b',
            r'\bgreat response\b'
        ]

        # Conversation ending patterns (dedicated category for auto-disconnect)
        self.ending_patterns = [
            r'\b(bye|goodbye|see you|talk to you later|have a good day|farewell)\b',
            r'\b(end|stop|close|quit|exit|hang up|disconnect)\b',
            r'\b(that\'s all|nothing else|no more questions|all done|i\'m done)\b',
            r'\b(end (the |this )?(call|conversation|chat|session))\b',
            r'\b(gotta go|have to go|need to go)\b',
            r'\b(catch you later|see ya|later|peace out)\b',
        ]

        # Add custom patterns if provided
        if custom_patterns:
            self.greeting_patterns.extend(custom_patterns.get("greeting", []))
            self.feedback_patterns.extend(custom_patterns.get("feedback", []))
            self.ending_patterns.extend(custom_patterns.get("ending", []))

        logger.info("Initialized Input Analyzer")

    def is_greeting_or_feedback(self, text: str) -> bool:
        """Check if the user input is a greeting or feedback.
        
        Args:
            text: The user input text to analyze
            
        Returns:
            True if it's a greeting/feedback, False if it needs RAG processing
        """
        text_lower = text.lower().strip()

        # Check if it's a greeting
        for pattern in self.greeting_patterns:
            if re.search(pattern, text_lower):
                logger.debug(f"Matched greeting pattern: {pattern}")
                return True

        # Check if it's feedback
        for pattern in self.feedback_patterns:
            if re.search(pattern, text_lower):
                logger.debug(f"Matched feedback pattern: {pattern}")
                return True

        return False

    def is_conversation_ending(self, text: str) -> bool:
        """Check if the user wants to end the conversation.

        Args:
            text: The user input text to analyze

        Returns:
            True if the user wants to end the conversation, False otherwise
        """
        text_lower = text.lower().strip()

        # Check if it matches ending patterns
        for pattern in self.ending_patterns:
            if re.search(pattern, text_lower):
                logger.info(f"Conversation ending detected with pattern: {pattern}")
                return True

        return False

    def analyze_input(self, user_input: str) -> Literal["normal_conversation", "needs_rag", "end_conversation"]:
        """Analyze user input to determine processing type.

        Args:
            user_input: The user's input text to analyze

        Returns:
            "end_conversation" for goodbye/ending intent,
            "normal_conversation" for greetings/feedback,
            "needs_rag" for complex questions
        """
        logger.info(f"Analyzing user input: {user_input}")

        # Check for conversation ending first (highest priority)
        if self.is_conversation_ending(user_input):
            result = "end_conversation"
            logger.info("Classified as: Conversation ending")
        elif self.is_greeting_or_feedback(user_input):
            result = "normal_conversation"
            logger.info("Classified as: Normal conversation (greeting/feedback)")
        else:
            result = "needs_rag"
            logger.info("Classified as: Needs RAG processing")

        return result

    def get_input_type_details(self, user_input: str) -> Dict[str, Any]:
        """Get detailed analysis of the input type.
        
        Args:
            user_input: The user's input text to analyze
            
        Returns:
            Dictionary containing detailed analysis results
        """
        result = {
            "input": user_input,
            "type": self.analyze_input(user_input),
            "matched_patterns": [],
            "confidence": 0.0
        }

        text_lower = user_input.lower().strip()

        # Check which patterns matched
        for pattern in self.greeting_patterns:
            if re.search(pattern, text_lower):
                result["matched_patterns"].append({"type": "greeting", "pattern": pattern})

        for pattern in self.feedback_patterns:
            if re.search(pattern, text_lower):
                result["matched_patterns"].append({"type": "feedback", "pattern": pattern})

        # Calculate confidence based on pattern matches
        if result["matched_patterns"]:
            result["confidence"] = 0.9  # High confidence for pattern matches
        else:
            result["confidence"] = 0.8  # Medium confidence for RAG classification

        return result

    def add_custom_pattern(self, pattern_type: str, pattern: str) -> None:
        """Add a custom pattern for input classification.
        
        Args:
            pattern_type: Type of pattern ("greeting" or "feedback")
            pattern: The regex pattern to add
        """
        if pattern_type == "greeting":
            self.greeting_patterns.append(pattern)
        elif pattern_type == "feedback":
            self.feedback_patterns.append(pattern)
        else:
            raise ValueError(f"Unsupported pattern type: {pattern_type}")

        logger.info(f"Added custom {pattern_type} pattern: {pattern}")

    def get_patterns(self) -> Dict[str, List[str]]:
        """Get all current patterns.
        
        Returns:
            Dictionary containing all patterns by type
        """
        return {
            "greeting": self.greeting_patterns,
            "feedback": self.feedback_patterns
        }
