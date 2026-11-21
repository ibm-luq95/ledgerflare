# -*- coding: utf-8 -*-#
from __future__ import annotations

import pytest

from core.utils.html_sanitizer import sanitize_html


class TestHTMLSanitizer:
    """Test suite for nh3 HTML sanitization utility."""

    def test_clean_html_remains_intact(self) -> None:
        raw_html = "<p>Hello <strong>world</strong>!</p>"
        cleaned = sanitize_html(raw_html)
        assert "Hello" in cleaned
        assert "<strong>world</strong>" in cleaned

    def test_strips_script_tags(self) -> None:
        raw_html = "<p>Text</p><script>alert('XSS');</script>"
        cleaned = sanitize_html(raw_html)
        assert "<script>" not in cleaned
        assert "alert" not in cleaned

    def test_strips_event_handlers(self) -> None:
        raw_html = "<img src='x' onerror='alert(1)'>"
        cleaned = sanitize_html(raw_html)
        assert "onerror" not in cleaned

    def test_strips_javascript_urls(self) -> None:
        raw_html = "<a href='javascript:alert(1)'>Click me</a>"
        cleaned = sanitize_html(raw_html)
        assert "javascript:" not in cleaned

    def test_enforces_rel_noopener(self) -> None:
        raw_html = "<a href='https://example.com' target='_blank'>External</a>"
        cleaned = sanitize_html(raw_html)
        assert 'rel="noopener noreferrer"' in cleaned

    def test_handles_empty_or_none(self) -> None:
        assert sanitize_html(None) == ""
        assert sanitize_html("") == ""
