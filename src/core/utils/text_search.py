"""Multilingual text search normalization utilities."""

from __future__ import annotations

import re
import unicodedata


_ARABIC_TASHKEEL_RE = re.compile(r"[\u064B-\u0652\u0670\u0640]")


def normalize_search_string(text: str) -> str:
    """Normalize text using NFKD, accent stripping, and case folding."""
    if not text:
        return ""

    s = _ARABIC_TASHKEEL_RE.sub("", text)
    s = re.sub(r"[إأآٱ]", "ا", s)  # noqa: RUF001
    s = re.sub(r"ة", "ه", s)  # noqa: RUF001
    s = re.sub(r"[ىي]", "ي", s)

    decomposed = unicodedata.normalize("NFKD", s)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))

    folded = stripped.casefold()
    return " ".join(folded.split())


def search_in_text(query: str, target: str) -> bool:
    """Perform normalized in-memory substring matching."""
    if not query:
        return True
    if not target:
        return False

    norm_query = normalize_search_string(query)
    norm_target = normalize_search_string(target)
    return norm_query in norm_target
