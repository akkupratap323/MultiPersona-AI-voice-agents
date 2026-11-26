"""
Unit tests for TextFilterProcessor.clean_text_for_speech.
"""

import pytest

from app.processors.text_filter_processor import TextFilterProcessor


@pytest.fixture
def text_filter():
    return TextFilterProcessor()


def _stream(text_filter, tokens):
    """Clean each streamed LLM token on its own and join them, as TTS hears it."""
    return "".join(text_filter.clean_text_for_speech(token) for token in tokens)


class TestStreamedWhitespace:
    """A token's surrounding whitespace keeps the words around it apart."""

    @pytest.mark.parametrize(
        "token, expected",
        [
            ("\n\n", " "),
            ("\n", " "),
            (" ", " "),
            ("Services\n", "Services "),
            ("agents.\n\n", "agents. "),
            (" word", " word"),
            (" word \n ", " word "),
        ],
    )
    def test_token_keeps_one_space_for_its_whitespace(self, text_filter, token, expected):
        assert text_filter.clean_text_for_speech(token) == expected

    def test_newline_tokens_do_not_join_words(self, text_filter):
        tokens = [
            "**",
            "Services",
            "**",
            "\n\n",
            "We",
            " offer",
            " voice",
            " agents",
            ".",
            "\n",
            "Ask",
            " me",
            ".",
        ]
        assert _stream(text_filter, tokens) == "Services We offer voice agents. Ask me."

    def test_markdown_list_items_stay_separate(self, text_filter):
        tokens = ["We", " build", ":\n", "- ", "Voice", " agents", "\n", "- ", "Chat", " bots"]
        assert _stream(text_filter, tokens) == "We build: Voice agents Chat bots"


class TestMarkdownCleanup:
    """Controls: markdown is still removed and spaces still collapse."""

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("**Bold** and *italic*", "Bold and italic"),
            ("## Header", "Header"),
            ("[Docs](https://example.com)", "Docs"),
            ("one    two", "one two"),
            ("Tom & Jerry", "Tom and Jerry"),
            ("", ""),
        ],
    )
    def test_cleans_markdown(self, text_filter, text, expected):
        assert text_filter.clean_text_for_speech(text) == expected
