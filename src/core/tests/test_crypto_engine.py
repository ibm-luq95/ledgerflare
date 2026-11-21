"""Comprehensive tests for CryptoEngine, EncryptedCharField, multi-key fallback, and model ORM integration."""

from __future__ import annotations

import pytest
from cryptography.fernet import Fernet
from model_bakery import baker

from client_account.models import ClientAccountProxy
from core.crypto.engine import VERSION_PREFIX_V2, CryptoEngine
from staff_briefcase.models.accounts.staff_accounts import StaffAccounts


@pytest.mark.security
def test_crypto_engine_encrypt_decrypt_round_trip() -> None:
    """Verify CryptoEngine encrypts with v2$ header and decrypts cleanly."""
    secret = "MySuperSecret123!"
    encrypted = CryptoEngine.encrypt(secret)
    assert encrypted.startswith(VERSION_PREFIX_V2)
    assert CryptoEngine.decrypt(encrypted) == secret


@pytest.mark.security
def test_crypto_engine_multi_key_fallback(settings) -> None:
    """Verify CryptoEngine decrypts ciphertext using legacy keys in OLD_ENCRYPT_KEYS."""
    key_a = Fernet.generate_key()
    key_b = Fernet.generate_key()

    # Encrypt secret using key_a
    cipher_a = Fernet(key_a)
    token_a = cipher_a.encrypt(b"LegacySecretPass").decode("ascii")
    v2_ciphertext_key_a = f"{VERSION_PREFIX_V2}{token_a}"

    # Configure Django settings: key_b as primary, key_a as fallback
    settings.ENCRYPT_KEY = key_b
    settings.OLD_ENCRYPT_KEYS = [key_a]

    # CryptoEngine should seamlessly fall back to key_a and succeed!
    decrypted = CryptoEngine.decrypt(v2_ciphertext_key_a)
    assert decrypted == "LegacySecretPass"


@pytest.mark.security
def test_crypto_engine_invalid_key_returns_none() -> None:
    """Verify invalid ciphertext signature returns None cleanly without throwing exceptions."""
    bad_ciphertext = f"{VERSION_PREFIX_V2}gAAAAABbadsignaturestring12345="
    decrypted = CryptoEngine.decrypt(bad_ciphertext)
    assert decrypted is None


@pytest.mark.security
@pytest.mark.django_db
def test_encrypted_char_field_client_account_orm() -> None:
    """Verify EncryptedCharField transparently encrypts on DB save and decrypts on DB fetch."""
    secret = "ClientAccountSecretPass99!"
    account = baker.make(ClientAccountProxy, account_password=secret)

    # Reload from DB
    account.refresh_from_db()
    assert account.account_password == secret
    assert account.decrypted_account_password == secret


@pytest.mark.security
@pytest.mark.django_db
def test_encrypted_char_field_staff_account_orm() -> None:
    """Verify EncryptedCharField transparently encrypts StaffAccounts password."""
    secret = "StaffAccountSecretPass88!"
    staff_acc = baker.make(StaffAccounts, password=secret)

    # Reload from DB
    staff_acc.refresh_from_db()
    assert staff_acc.password == secret
    assert staff_acc.decrypted_password == secret
