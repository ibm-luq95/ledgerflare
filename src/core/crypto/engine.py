"""Multi-key fallback cryptographic engine with version header support."""

from __future__ import annotations

import base64
import logging
from typing import List

from cryptography.fernet import Fernet, InvalidSignature, InvalidToken
from django.conf import settings


logger = logging.getLogger(__name__)

VERSION_PREFIX_V2 = "v2$"


class CryptoEngine:
    """Centralized cryptographic engine handling encryption format detection
    and multi-key fallback decryption.
    """

    @classmethod
    def get_keys(cls) -> list[str]:
        """Collect all active and legacy encryption keys."""
        keys: list[str] = []
        primary_key = getattr(settings, "ENCRYPT_KEY", None)
        if primary_key:
            keys.append(primary_key)

        old_keys = getattr(settings, "OLD_ENCRYPT_KEYS", [])
        if isinstance(old_keys, str):
            old_keys = [k.strip() for k in old_keys.split(",") if k.strip()]

        for k in old_keys:
            if k not in keys:
                keys.append(k)
        return keys

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """Encrypt plaintext string using current ENCRYPT_KEY with v2$ version header."""
        if not plaintext:
            return plaintext

        primary_key = getattr(settings, "ENCRYPT_KEY", None)
        if not primary_key:
            raise ValueError("ENCRYPT_KEY is not configured in Django settings.")

        cipher = Fernet(primary_key)
        token = cipher.encrypt(plaintext.encode("utf-8")).decode("ascii")
        return f"{VERSION_PREFIX_V2}{token}"

    @classmethod
    def decrypt(cls, ciphertext: str) -> str | None:
        """Decrypt ciphertext trying ENCRYPT_KEY first, then falling back to OLD_ENCRYPT_KEYS."""
        if not ciphertext:
            return None

        keys = cls.get_keys()
        if not keys:
            logger.warning("No encryption keys configured in settings.")
            return None

        is_v2 = ciphertext.startswith(VERSION_PREFIX_V2)
        payload_str = ciphertext[len(VERSION_PREFIX_V2):] if is_v2 else ciphertext

        for key in keys:
            try:
                cipher = Fernet(key)
                if is_v2:
                    return cipher.decrypt(payload_str.encode("ascii")).decode("utf-8")
                # Legacy double-base64 decoding fallback
                try:
                    raw_bytes = base64.urlsafe_b64decode(payload_str)
                except Exception:
                    raw_bytes = payload_str.encode("ascii")
                return cipher.decrypt(raw_bytes).decode("utf-8")
            except (InvalidToken, InvalidSignature, ValueError):
                continue
            except Exception as e:
                logger.warning("Unexpected error during decryption key trial: %s", str(e))
                continue

        logger.warning("Decryption failed: signature did not match any active or legacy key.")
        return None
