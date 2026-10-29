from __future__ import annotations

import pytest

from core.crypto.engine import CryptoEngine
from core.crypto.service import (
    DecryptionIntegrityError,
    EncryptionService,
    KeyConfigurationError,
)


@pytest.mark.unit
def test_aes_gcm_roundtrip() -> None:
    aad = b"Task:additional_notes:123e4567-e89b-12d3-a456-426614174000"
    plaintext = "Sensitive financial note: $50,000 disbursement"
    ciphertext = EncryptionService.encrypt(plaintext, aad)

    assert ciphertext.startswith("v1:")
    decrypted = EncryptionService.decrypt(ciphertext, aad)
    assert decrypted == plaintext


@pytest.mark.unit
def test_aes_gcm_aad_tamper_fails() -> None:
    aad1 = b"Task:additional_notes:123e4567-e89b-12d3-a456-426614174000"
    aad2 = b"Task:additional_notes:999e4567-e89b-12d3-a456-426614174999"
    ciphertext = EncryptionService.encrypt("Secret", aad1)

    with pytest.raises(DecryptionIntegrityError):
        EncryptionService.decrypt(ciphertext, aad2)


@pytest.mark.unit
def test_aes_gcm_bit_flip_fails() -> None:
    aad = b"Task:additional_notes:123e4567-e89b-12d3-a456-426614174000"
    ciphertext = EncryptionService.encrypt("Secret", aad)
    parts = ciphertext.split(":")
    corrupt_ct = parts[3][:-2] + ("A" if parts[3][-1] != "A" else "B")
    tampered = f"{parts[0]}:{parts[1]}:{parts[2]}:{corrupt_ct}:{parts[4]}"

    with pytest.raises(DecryptionIntegrityError):
        EncryptionService.decrypt(tampered, aad)


@pytest.mark.unit
def test_legacy_fernet_fallback() -> None:
    fernet_token = CryptoEngine.encrypt("legacy_password_123")
    aad = b"ClientAccount:account_password:123e4567-e89b-12d3-a456-426614174000"
    decrypted = EncryptionService.decrypt(fernet_token, aad)
    assert decrypted == "legacy_password_123"


@pytest.mark.unit
def test_bytes_encryption_roundtrip() -> None:
    aad = b"Document:file:123e4567-e89b-12d3-a456-426614174000"
    raw_data = b"%PDF-1.4\x00\x01\x02Confidential Report Bytes\xff\xfe"
    encrypted = EncryptionService.encrypt_bytes(raw_data, aad)
    decrypted = EncryptionService.decrypt_bytes(encrypted, aad)
    assert decrypted == raw_data


@pytest.mark.unit
def test_bytes_tamper_fails() -> None:
    aad = b"Document:file:123e4567-e89b-12d3-a456-426614174000"
    encrypted = bytearray(EncryptionService.encrypt_bytes(b"Clean", aad))
    encrypted[-1] ^= 0x01
    with pytest.raises(DecryptionIntegrityError):
        EncryptionService.decrypt_bytes(bytes(encrypted), aad)


@pytest.mark.unit
def test_empty_and_whitespace_plaintext() -> None:
    aad = b"Task:hints:dummy-id"
    assert EncryptionService.encrypt("", aad) == ""
    # Whitespace-only string must still be encrypted
    ws_cipher = EncryptionService.encrypt("   \t\n  ", aad)
    assert ws_cipher.startswith("v1:")
    assert EncryptionService.decrypt(ws_cipher, aad) == "   \t\n  "


@pytest.mark.unit
def test_empty_ciphertext_raises() -> None:
    aad = b"Task:hints:dummy-id"
    with pytest.raises(DecryptionIntegrityError):
        EncryptionService.decrypt("", aad)


@pytest.mark.unit
def test_malformed_envelope_structure_raises() -> None:
    aad = b"Task:hints:dummy-id"
    # Not enough segments
    with pytest.raises(DecryptionIntegrityError):
        EncryptionService.decrypt("v1:k1:missing_parts", aad)

    # Too many segments
    with pytest.raises(DecryptionIntegrityError):
        EncryptionService.decrypt("v1:k1:part1:part2:part3:part4", aad)


@pytest.mark.unit
def test_invalid_base64_raises() -> None:
    aad = b"Task:hints:dummy-id"
    # Invalid characters in base64 segment
    with pytest.raises(DecryptionIntegrityError):
        EncryptionService.decrypt("v1:k1:!!!invalid!!!:valid:valid", aad)


@pytest.mark.unit
def test_invalid_nonce_or_tag_length_raises() -> None:
    aad = b"Task:hints:dummy-id"
    # Valid base64 but decoded nonce is not 12 bytes
    short_nonce = "AQID"  # 3 bytes
    valid_tag = "AAAAAAAAAAAAAAAAAAAAAA=="  # 16 bytes
    with pytest.raises(DecryptionIntegrityError):
        EncryptionService.decrypt(f"v1:k1:{short_nonce}:c29tZWN0:{valid_tag}", aad)


@pytest.mark.unit
def test_unrecognized_garbage_ciphertext_raises() -> None:
    aad = b"Task:hints:dummy-id"
    with pytest.raises(DecryptionIntegrityError):
        EncryptionService.decrypt("completely_random_garbage_data", aad)


@pytest.mark.unit
def test_unicode_complex_strings() -> None:
    aad = b"Task:hints:unicode-test"
    complex_text = (
        "مرحبا بالعالم 🌍 🚀 💥 Special symbols: §±!@#$%^&*()_+ Null byte: \x00 End."
    )
    ciphertext = EncryptionService.encrypt(complex_text, aad)
    assert EncryptionService.decrypt(ciphertext, aad) == complex_text


@pytest.mark.unit
def test_key_configuration_errors(settings: pytest.SettingsWrapper) -> None:
    # Key not set
    settings.CONTENT_ENCRYPTION_KEY = None
    settings.CONTENT_ENCRYPTION_KEYS = {}
    with pytest.raises(KeyConfigurationError):
        EncryptionService._get_key_bytes()

    # Key too short
    settings.CONTENT_ENCRYPTION_KEY = b"short_key_16byte"
    settings.CONTENT_ENCRYPTION_KEYS = {}
    with pytest.raises(KeyConfigurationError):
        EncryptionService._get_key_bytes()

    # Invalid hex string
    settings.CONTENT_ENCRYPTION_KEY = "Z" * 64
    settings.CONTENT_ENCRYPTION_KEYS = {}
    with pytest.raises(KeyConfigurationError):
        EncryptionService._get_key_bytes()
