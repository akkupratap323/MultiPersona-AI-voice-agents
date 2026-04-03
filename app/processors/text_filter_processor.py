"""Text Filter Processor for cleaning LLM output before TTS.

This processor removes markdown formatting and other unwanted symbols
that TTS would read aloud (e.g., asterisks, hashtags, brackets).
"""

import re
from typing import Optional

from loguru import logger
from pipecat.frames.frames import Frame, TextFrame, StartFrame, EndFrame, CancelFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

# Phrases that signal laughter — bot will inject [laughter] before the next word
_LAUGHTER_TRIGGERS = re.compile(
    r'\b('
    r'ha ha|haha|hehe|he he|lol|lmao|hah|heeh|'
    r'that\'?s funny|how funny|pretty funny|quite funny|rather funny|'
    r'that\'?s hilarious|how hilarious|absolutely hilarious|'
    r'that\'?s amusing|how amusing|'
    r'can\'?t help (but )?laugh|have to laugh|can\'?t stop laughing|'
    r'laugh(ing)? at that|burst(ing)? out laughing|'
    r'tickles? me|that cracks? me up|quite the joke|'
    r'joke(s|d)?|joking aside|in all seriousness.*just kidding'
    r')\b',
    re.IGNORECASE
)


class TextFilterProcessor(FrameProcessor):
    """Processor that filters markdown and unwanted symbols from text before TTS.

    This processor sits in the pipeline between LLM and TTS to clean up
    markdown formatting that would otherwise be read aloud as words like
    "star star" or "hashtag".

    When using Cartesia TTS, it also injects [laughter] tags automatically
    when the bot response contains humorous language.

    Attributes:
        enabled: Whether filtering is enabled
        inject_laughter: Whether to inject [laughter] tags for Cartesia TTS
    """

    def __init__(self, enabled: bool = True, inject_laughter: bool = False):
        """Initialize the Text Filter Processor.

        Args:
            enabled: Whether text filtering is enabled
            inject_laughter: Inject [laughter] tags when bot says something funny
                             (Cartesia sonic-3 only — other TTS will read it aloud)
        """
        super().__init__()
        self.enabled = enabled
        self.inject_laughter = inject_laughter
        self._started = False
        logger.info(f"TextFilterProcessor initialized (enabled={enabled}, inject_laughter={inject_laughter})")

    def clean_text_for_speech(self, text: str) -> str:
        """Clean text by removing markdown and unwanted symbols.

        Removes:
        - Bold markers: **text** or __text__ → text
        - Italic markers: *text* or _text_ → text
        - Bullet points: * item or - item → item
        - Headers: ## Header → Header
        - Links: [text](url) → text
        - Code blocks: `code` → code
        - Strikethrough: ~~text~~ → text

        Args:
            text: Original text with markdown formatting

        Returns:
            Cleaned text suitable for TTS
        """
        if not text:
            return text

        original_text = text

        # Remove code blocks (```code```)
        text = re.sub(r'```[\s\S]*?```', '', text)

        # Remove inline code (`code`)
        text = re.sub(r'`([^`]+)`', r'\1', text)

        # Remove links but keep link text: [text](url) → text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # Remove bold: **text** or __text__ → text
        text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)

        # Remove italic: *text* or _text_ → text
        text = re.sub(r'\*([^\*]+)\*', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)

        # Remove strikethrough: ~~text~~ → text
        text = re.sub(r'~~([^~]+)~~', r'\1', text)

        # Remove headers: ## Header → Header
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

        # Remove bullet points at start of lines: * item or - item → item
        text = re.sub(r'^\s*[\*\-]\s+', '', text, flags=re.MULTILINE)

        # Remove remaining standalone asterisks or underscores
        text = re.sub(r'\*+', '', text)
        text = re.sub(r'_+', '', text)

        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)

        # Clean up multiple newlines
        text = re.sub(r'\n\s*\n', '\n', text)

        # Strip leaked LLM function call syntax (Llama native format)
        # e.g. <function=call_rag_system>{"question": "..."}</function>
        # Also handles multi-line JSON bodies in the function tag
        text = re.sub(r'<function=[^>]*>[\s\S]*?</function>', '', text)
        text = re.sub(r'function=\w+\{[^}]*\}', '', text)

        # Escape XML/SSML special characters to prevent TTS errors
        # The & character must be escaped FIRST (before other escapes that use &)
        text = text.replace('&', ' and ')  # Replace & with "and" for natural speech
        text = text.replace('<', ' ')  # Replace < with space (preserves word boundaries)
        text = text.replace('>', ' ')  # Replace > with space (preserves word boundaries)

        # Clean up multiple spaces (again, after bracket removal may have added extra spaces)
        text = re.sub(r'\s+', ' ', text)

        # Strip trailing whitespace only — preserve leading spaces for word separation
        # in streaming mode (LLM tokens arrive as " word" with leading space)
        text = text.rstrip()

        if text != original_text:
            logger.debug(f"Filtered text: '{original_text[:50]}...' → '{text[:50]}...'")

        # Inject [laughter] tag for Cartesia TTS when bot says something funny
        if self.inject_laughter and text:
            text = self._inject_laughter_tags(text)

        return text

    def _inject_laughter_tags(self, text: str) -> str:
        """Inject Cartesia [laughter] nonverbalism tag when humorous phrases are detected.

        Inserts [laughter] immediately after the triggering phrase so Cartesia
        produces a natural laugh at that point in the audio stream.

        Args:
            text: Cleaned TTS text

        Returns:
            Text with [laughter] tags injected where appropriate
        """
        def _insert_after_match(m: re.Match) -> str:
            return m.group(0) + " [laughter]"

        result = _LAUGHTER_TRIGGERS.sub(_insert_after_match, text)
        if result != text:
            logger.info(f"[LAUGHTER] Injected [laughter] tag: '{text[:60]}...' → '{result[:70]}...'")
        return result

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process frames and filter TextFrames.

        Args:
            frame: The frame to process
            direction: The direction of frame processing
        """
        # Handle lifecycle frames (StartFrame, EndFrame, etc.)
        await super().process_frame(frame, direction)

        # Only filter text frames going downstream (to TTS)
        if isinstance(frame, TextFrame) and direction == FrameDirection.DOWNSTREAM:
            if self.enabled and frame.text:
                # Clean the text and create new frame
                cleaned_text = self.clean_text_for_speech(frame.text)
                await self.push_frame(TextFrame(cleaned_text), direction)
            else:
                await self.push_frame(frame, direction)
        else:
            # Pass all other frames through unchanged
            await self.push_frame(frame, direction)

    def enable(self) -> None:
        """Enable text filtering."""
        self.enabled = True
        logger.info("TextFilterProcessor enabled")

    def disable(self) -> None:
        """Disable text filtering."""
        self.enabled = False
        logger.info("TextFilterProcessor disabled")
