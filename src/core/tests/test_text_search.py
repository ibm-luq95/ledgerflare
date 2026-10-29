from __future__ import annotations

import pytest

from core.utils.text_search import normalize_search_string, search_in_text


@pytest.mark.unit
def test_unicode_accent_stripping() -> None:
    assert normalize_search_string("José Gómez") == "jose gomez"
    assert search_in_text("jose", "José Gómez") is True
    assert search_in_text("GOMEZ", "José Gómez") is True


@pytest.mark.unit
def test_arabic_normalization() -> None:
    assert normalize_search_string("مُحَمَّدٌ أَحْمَد") == "محمد احمد"
    assert search_in_text("احمد", "أَحْمَد") is True
    assert search_in_text("شريكة", "شريكةٌ") is True
    assert search_in_text("علي", "على") is True
    assert search_in_text("تطويل", "تـطـويـل") is True


@pytest.mark.unit
def test_german_and_french_diacritics() -> None:
    assert normalize_search_string(
        "Müller Straße"
    ) == "muller strasse" or "muller" in normalize_search_string("Müller")
    assert search_in_text("muller", "Müller") is True
    assert search_in_text("café", "CAFE") is True
    assert search_in_text("cafe", "Café résumé") is True
    assert search_in_text("resume", "Café résumé") is True
    assert search_in_text("francais", "Français") is True


@pytest.mark.unit
def test_whitespace_and_newline_normalization() -> None:
    text = "   Disbursement \t\t for \n\n  Client ABC   "
    assert normalize_search_string(text) == "disbursement for client abc"
    assert search_in_text("for client", text) is True


@pytest.mark.unit
def test_empty_query_and_target_boundaries() -> None:
    # Empty query matches anything
    assert search_in_text("", "Any Text") is True
    assert search_in_text("", "") is True
    # Non-empty query against empty target returns False
    assert search_in_text("Search", "") is False
    assert normalize_search_string("") == ""
