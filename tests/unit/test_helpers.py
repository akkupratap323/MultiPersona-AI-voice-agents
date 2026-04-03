"""
Unit tests for utility helper functions.
"""

import pytest
from app.utils.helpers import (
    generate_session_id,
    format_duration,
    safe_json_loads,
    merge_dicts,
    truncate_text,
    normalize_text,
)


class TestGenerateSessionId:
    """Tests for generate_session_id function."""

    def test_default_prefix(self):
        """Test session ID with default prefix."""
        session_id = generate_session_id()
        assert session_id.startswith("session_")

    def test_custom_prefix(self):
        """Test session ID with custom prefix."""
        session_id = generate_session_id(prefix="test")
        assert session_id.startswith("test_")

    def test_uniqueness(self):
        """Test that generated IDs are unique."""
        ids = [generate_session_id() for _ in range(100)]
        assert len(ids) == len(set(ids))


class TestFormatDuration:
    """Tests for format_duration function."""

    def test_microseconds(self):
        """Test formatting microseconds."""
        result = format_duration(0.0001)
        assert "us" in result

    def test_milliseconds(self):
        """Test formatting milliseconds."""
        result = format_duration(0.5)
        assert "ms" in result

    def test_seconds(self):
        """Test formatting seconds."""
        result = format_duration(30)
        assert "s" in result
        assert "m" not in result

    def test_minutes(self):
        """Test formatting minutes."""
        result = format_duration(120)
        assert "m" in result

    def test_hours(self):
        """Test formatting hours."""
        result = format_duration(3700)
        assert "h" in result


class TestSafeJsonLoads:
    """Tests for safe_json_loads function."""

    def test_valid_json(self):
        """Test parsing valid JSON."""
        result = safe_json_loads('{"key": "value"}')
        assert result == {"key": "value"}

    def test_invalid_json(self):
        """Test handling invalid JSON."""
        result = safe_json_loads("not json")
        assert result == {}

    def test_custom_default(self):
        """Test custom default value."""
        result = safe_json_loads("not json", default=[])
        assert result == []


class TestMergeDicts:
    """Tests for merge_dicts function."""

    def test_simple_merge(self):
        """Test simple dictionary merge."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = merge_dicts(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_deep_merge(self):
        """Test deep merge of nested dictionaries."""
        base = {"outer": {"a": 1, "b": 2}}
        override = {"outer": {"b": 3, "c": 4}}
        result = merge_dicts(base, override)
        assert result == {"outer": {"a": 1, "b": 3, "c": 4}}

    def test_original_unchanged(self):
        """Test that original dictionaries are not modified."""
        base = {"a": 1}
        override = {"b": 2}
        merge_dicts(base, override)
        assert base == {"a": 1}


class TestTruncateText:
    """Tests for truncate_text function."""

    def test_short_text(self):
        """Test text shorter than max length."""
        result = truncate_text("Hello", max_length=10)
        assert result == "Hello"

    def test_long_text(self):
        """Test text longer than max length."""
        result = truncate_text("Hello World!", max_length=8)
        assert len(result) == 8
        assert result.endswith("...")

    def test_custom_suffix(self):
        """Test custom truncation suffix."""
        result = truncate_text("Hello World!", max_length=10, suffix="…")
        assert result.endswith("…")


class TestNormalizeText:
    """Tests for normalize_text function."""

    def test_whitespace_normalization(self):
        """Test whitespace normalization."""
        result = normalize_text("  hello   world  ")
        assert result == "hello world"

    def test_unicode_normalization(self):
        """Test Unicode normalization."""
        result = normalize_text("ﬁne")  # fi ligature
        assert "fi" in result or "ﬁ" in result
