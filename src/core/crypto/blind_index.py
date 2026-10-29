"""HMAC-SHA256 blind index generator for searchable encrypted fields."""

from __future__ import annotations

import hashlib
import hmac

from django.conf import settings

from core.crypto.service import KeyConfigurationError
from core.utils.text_search import normalize_search_string


def get_blind_index_key() -> bytes:
    """Retrieve and validate the HMAC pepper key for blind indexing."""
    raw_key = getattr(settings, "BLIND_INDEX_KEY", None)
    if not raw_key:
        raw_key = getattr(settings, "CONTENT_ENCRYPTION_KEY", None)

    if not raw_key:
        msg = "Neither BLIND_INDEX_KEY nor CONTENT_ENCRYPTION_KEY is configured."
        raise KeyConfigurationError(msg)

    if isinstance(raw_key, bytes):
        return raw_key

    clean_key = str(raw_key).strip()
    if len(clean_key) == 64:
        try:
            return bytes.fromhex(clean_key)
        except ValueError:
            pass

    return clean_key.encode("utf-8")


def compute_blind_index(
    text: str | None,
    context: str = "",
    normalize: bool = True,
) -> str:
    """Compute a deterministic HMAC-SHA256 blind index digest for exact lookups."""
    if not text:
        return ""

    val = normalize_search_string(text) if normalize else text
    key = get_blind_index_key()
    message = f"{context}:{val}".encode() if context else val.encode()
    return hmac.new(key, message, hashlib.sha256).hexdigest()
