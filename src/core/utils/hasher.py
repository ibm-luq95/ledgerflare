# -*- coding: utf-8 -*-#
from __future__ import annotations

from core.crypto.engine import CryptoEngine


class PasswordHasher:
    """Backward-compatibility wrapper over CryptoEngine."""

    @staticmethod
    def encrypt(pas: str) -> str:
        """Encrypt password using CryptoEngine."""
        return CryptoEngine.encrypt(pas)

    @staticmethod
    def decrypt(pas: str, env_key: str | None = None) -> str | None:
        """Decrypt password using CryptoEngine with multi-key fallback."""
        return CryptoEngine.decrypt(pas)
