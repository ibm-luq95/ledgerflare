"""Authenticated crypto service supporting AES-256-GCM and Fernet fallback."""

from __future__ import annotations

import base64
import binascii
import os
import re
from typing import Any, ClassVar

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings

from core.crypto.engine import CryptoEngine


class DecryptionIntegrityError(Exception):
    """Raised when ciphertext integrity check fails or envelope is invalid."""


class KeyConfigurationError(Exception):
    """Raised when encryption key is missing or improperly sized."""


class EncryptionService:
    """Core cryptographic service providing AES-256-GCM encryption with AAD binding."""

    VERSION_PREFIX_V1: ClassVar[str] = "v1:"
    STORAGE_MAGIC_HEADER: ClassVar[bytes] = b"LFENC01"
    NONCE_SIZE_BYTES: ClassVar[int] = 12
    TAG_SIZE_BYTES: ClassVar[int] = 16

    @classmethod
    def _parse_raw_key(cls, raw_key: Any, key_id: str) -> bytes:
        if isinstance(raw_key, bytes):
            key_bytes = raw_key
        elif isinstance(raw_key, str):
            clean_key = raw_key.strip()
            if len(clean_key) == 64:
                try:
                    key_bytes = bytes.fromhex(clean_key)
                except ValueError as err:
                    msg = f"Invalid hex key format for key ID '{key_id}'."
                    raise KeyConfigurationError(msg) from err
            else:
                try:
                    key_bytes = base64.urlsafe_b64decode(clean_key)
                except ValueError, binascii.Error:
                    key_bytes = clean_key.encode("utf-8")
        else:
            msg = f"Unsupported key type for key ID '{key_id}'."
            raise KeyConfigurationError(msg)

        if len(key_bytes) != 32:
            msg = (
                f"Encryption key '{key_id}' must be exactly 32 bytes (256 bits), "
                f"got {len(key_bytes)} bytes."
            )
            raise KeyConfigurationError(msg)
        return key_bytes

    @classmethod
    def _get_key_bytes(cls, key_id: str | None = None) -> tuple[str, bytes]:
        keys_dict: dict[str, str] = getattr(settings, "CONTENT_ENCRYPTION_KEYS", {})
        active_id: str = getattr(settings, "ACTIVE_KEY_ID", "k1")
        target_id: str = key_id if key_id is not None else active_id

        if not re.match(r"^[a-zA-Z0-9_-]+$", target_id):
            msg = f"Invalid key identifier format: '{target_id}'."
            raise KeyConfigurationError(msg)

        raw_key = None
        if keys_dict and target_id in keys_dict:
            raw_key = keys_dict[target_id]
        elif target_id == "k1" and getattr(settings, "CONTENT_ENCRYPTION_KEY", None):
            raw_key = settings.CONTENT_ENCRYPTION_KEY

        if not raw_key:
            msg = f"Encryption key ID '{target_id}' is not configured."
            raise KeyConfigurationError(msg)

        key_bytes = cls._parse_raw_key(raw_key, target_id)
        return target_id, key_bytes

    @classmethod
    def encrypt(
        cls, plaintext: str, associated_data: bytes, key_id: str | None = None
    ) -> str:
        """Encrypt plaintext string using AES-256-GCM with AAD binding."""
        if not plaintext:
            return plaintext

        active_id, key = cls._get_key_bytes(key_id=key_id)
        aesgcm = AESGCM(key)
        nonce = os.urandom(cls.NONCE_SIZE_BYTES)
        data_bytes = plaintext.encode("utf-8")

        ciphertext_with_tag = aesgcm.encrypt(nonce, data_bytes, associated_data)
        ciphertext = ciphertext_with_tag[: -cls.TAG_SIZE_BYTES]
        tag = ciphertext_with_tag[-cls.TAG_SIZE_BYTES :]

        b64_nonce = base64.urlsafe_b64encode(nonce).decode("ascii")
        b64_ct = base64.urlsafe_b64encode(ciphertext).decode("ascii")
        b64_tag = base64.urlsafe_b64encode(tag).decode("ascii")

        return f"{cls.VERSION_PREFIX_V1}{active_id}:{b64_nonce}:{b64_ct}:{b64_tag}"

    @classmethod
    def decrypt(cls, ciphertext: str, associated_data: bytes) -> str:
        """Decrypt AES-256-GCM or legacy Fernet ciphertext with AAD validation."""
        if not ciphertext:
            msg = "Empty ciphertext provided."
            raise DecryptionIntegrityError(msg)

        if ciphertext.startswith(cls.VERSION_PREFIX_V1):
            parts = ciphertext.split(":")
            if len(parts) != 5:
                msg = "Malformed v1 envelope structure."
                raise DecryptionIntegrityError(msg)

            _, key_id, b64_nonce, b64_ct, b64_tag = parts
            try:
                nonce = base64.urlsafe_b64decode(b64_nonce.encode("ascii"))
                ct = base64.urlsafe_b64decode(b64_ct.encode("ascii"))
                tag = base64.urlsafe_b64decode(b64_tag.encode("ascii"))
            except (ValueError, binascii.Error) as err:
                msg = "Invalid base64 encoding."
                raise DecryptionIntegrityError(msg) from err

            if len(nonce) != cls.NONCE_SIZE_BYTES or len(tag) != cls.TAG_SIZE_BYTES:
                msg = "Invalid nonce or tag length."
                raise DecryptionIntegrityError(msg)

            _, key = cls._get_key_bytes(key_id=key_id)
            aesgcm = AESGCM(key)
            combined = ct + tag

            try:
                decrypted_bytes = aesgcm.decrypt(nonce, combined, associated_data)
                return decrypted_bytes.decode("utf-8")
            except (InvalidTag, ValueError, UnicodeDecodeError) as err:
                msg = "Decryption integrity check failed."
                raise DecryptionIntegrityError(msg) from err

        legacy_result = CryptoEngine.decrypt(ciphertext)
        if legacy_result is not None:
            return legacy_result

        msg = "Ciphertext did not match active or legacy format."
        raise DecryptionIntegrityError(msg)

    @classmethod
    def encrypt_bytes(
        cls, data: bytes, associated_data: bytes, key_id: str | None = None
    ) -> bytes:
        """Encrypt raw binary data for storage."""
        _, key = cls._get_key_bytes(key_id=key_id)
        aesgcm = AESGCM(key)
        nonce = os.urandom(cls.NONCE_SIZE_BYTES)
        encrypted_payload = aesgcm.encrypt(nonce, data, associated_data)
        return cls.STORAGE_MAGIC_HEADER + nonce + encrypted_payload

    @classmethod
    def decrypt_bytes(
        cls, ciphertext: bytes, associated_data: bytes, key_id: str | None = None
    ) -> bytes:
        """Decrypt binary storage payload and verify magic header."""
        header_len = len(cls.STORAGE_MAGIC_HEADER)
        min_len = header_len + cls.NONCE_SIZE_BYTES + cls.TAG_SIZE_BYTES
        if len(ciphertext) < min_len or not ciphertext.startswith(
            cls.STORAGE_MAGIC_HEADER
        ):
            msg = "Invalid encrypted bytes magic header or truncated payload."
            raise DecryptionIntegrityError(msg)

        nonce = ciphertext[header_len : header_len + cls.NONCE_SIZE_BYTES]
        payload = ciphertext[header_len + cls.NONCE_SIZE_BYTES :]

        _, key = cls._get_key_bytes(key_id=key_id)
        aesgcm = AESGCM(key)
        try:
            return aesgcm.decrypt(nonce, payload, associated_data)
        except (InvalidTag, ValueError) as err:
            msg = "Decryption integrity check failed for binary payload."
            raise DecryptionIntegrityError(msg) from err
