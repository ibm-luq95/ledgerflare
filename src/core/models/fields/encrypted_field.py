"""Custom Django Model Field for transparent database encryption and decryption."""

from __future__ import annotations

from typing import Any

from django.db import models

from core.crypto.engine import VERSION_PREFIX_V2, CryptoEngine


class EncryptedCharField(models.CharField):
    """Django CharField that transparently encrypts data on DB save
    and decrypts data on DB fetch using CryptoEngine."""

    def from_db_value(self, value: Any, expression: Any, connection: Any) -> str | None:
        """Decrypt data when loaded from the database into Python attributes."""
        if not value:
            return value
        return CryptoEngine.decrypt(str(value))

    def get_prep_value(self, value: Any) -> str | None:
        """Encrypt data when preparing values to write into the database."""
        value = super().get_prep_value(value)
        if not value:
            return value
        if isinstance(value, str) and value.startswith(VERSION_PREFIX_V2):
            return value
        return CryptoEngine.encrypt(str(value))
