"""Tests for EncryptionService multi-key resolution, envelope parsing, and fallback."""

from __future__ import annotations

import os

import pytest

from core.crypto.service import (
    DecryptionIntegrityError,
    EncryptionService,
    KeyConfigurationError,
)


@pytest.fixture
def multi_key_settings(settings: pytest.MonkeyPatch) -> tuple[str, str]:
    """Configure settings with two 256-bit keys."""
    key_k1 = os.urandom(32).hex()
    key_k2 = os.urandom(32).hex()
    settings.CONTENT_ENCRYPTION_KEYS = {"k1": key_k1, "k2": key_k2}
    settings.ACTIVE_KEY_ID = "k2"
    settings.CONTENT_ENCRYPTION_KEY = key_k1
    return key_k1, key_k2


@pytest.mark.security
def test_encrypt_uses_active_key_id(multi_key_settings: tuple[str, str]) -> None:
    """Verify encrypt() stamps envelope with ACTIVE_KEY_ID (k2)."""
    aad = b"test:field:123"
    token = EncryptionService.encrypt("secret_message", aad)
    assert token.startswith("v1:k2:")
    assert EncryptionService.decrypt(token, aad) == "secret_message"


@pytest.mark.security
def test_decrypt_resolves_older_key_id(
    multi_key_settings: tuple[str, str], settings: pytest.MonkeyPatch
) -> None:
    """Verify decrypt() successfully reads v1:k1: envelope even when ACTIVE_KEY_ID is k2."""
    aad = b"test:field:123"
    settings.ACTIVE_KEY_ID = "k1"
    token_k1 = EncryptionService.encrypt("old_secret", aad)
    assert token_k1.startswith("v1:k1:")

    # Now switch active key to k2
    settings.ACTIVE_KEY_ID = "k2"
    # k1 token must still decrypt cleanly without errors
    assert EncryptionService.decrypt(token_k1, aad) == "old_secret"


@pytest.mark.security
def test_decrypt_unregistered_key_id_raises_error(
    multi_key_settings: tuple[str, str],
) -> None:
    """Verify decrypting an envelope referencing unregistered k99 raises KeyConfigurationError."""
    # 12-byte nonce base64: 'AAAAAAAAAAAAAAAA' (12 bytes)
    # ciphertext base64: 'AAAA'
    # 16-byte tag base64: 'AAAAAAAAAAAAAAAAAAAAAA==' (16 bytes)
    bad_token = "v1:k99:AAAAAAAAAAAAAAAA:AAAA:AAAAAAAAAAAAAAAAAAAAAA=="
    with pytest.raises(KeyConfigurationError, match="not configured"):
        EncryptionService.decrypt(bad_token, b"test:field:123")


@pytest.mark.security
def test_encrypt_with_explicit_key_id(multi_key_settings: tuple[str, str]) -> None:
    """Verify encrypt() supports specifying explicit key_id override."""
    aad = b"test:field:explicit"
    token = EncryptionService.encrypt("custom_key_message", aad, key_id="k1")
    assert token.startswith("v1:k1:")
    assert EncryptionService.decrypt(token, aad) == "custom_key_message"


@pytest.mark.security
def test_get_key_bytes_when_single_key_setting_is_none(
    settings: pytest.MonkeyPatch,
) -> None:
    """Verify _get_key_bytes retrieves k1 from CONTENT_ENCRYPTION_KEYS when CONTENT_ENCRYPTION_KEY is None."""
    key_k1 = os.urandom(32).hex()
    key_k2 = os.urandom(32).hex()
    settings.CONTENT_ENCRYPTION_KEYS = {"k1": key_k1, "k2": key_k2}
    settings.ACTIVE_KEY_ID = "k2"
    settings.CONTENT_ENCRYPTION_KEY = None

    target_id, key_bytes = EncryptionService._get_key_bytes("k1")
    assert target_id == "k1"
    assert key_bytes == bytes.fromhex(key_k1)
