"""Chunked encryption container engine (LFENC02) specification and cryptography."""

from __future__ import annotations

import math
import secrets
import struct
import uuid
from dataclasses import dataclass
from typing import Final

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from core.crypto.service import DecryptionIntegrityError


MAGIC: Final[bytes] = b"LFENC02\x00"
HEADER_SIZE: Final[int] = 84
HEADER_AAD_PREFIX: Final[bytes] = b"LFENC02:HEADER"
CHUNK_AAD_PREFIX: Final[bytes] = b"LFENC02:CHUNK:"
DEFAULT_CHUNK_SIZE: Final[int] = 1_048_576
CHUNK_OVERHEAD: Final[int] = 28


@dataclass(frozen=True, slots=True)
class ChunkedContainerHeader:
    """Header metadata for LFENC02 chunked container."""

    magic: bytes
    key_id: str
    chunk_size: int
    plaintext_size: int
    total_chunks: int
    file_uuid: bytes
    header_nonce: bytes
    header_tag: bytes


class ChunkedContainerEngine:
    """Engine handling LFENC02 container creation and chunk operations."""

    @staticmethod
    def get_chunk_offset(
        chunk_index: int, chunk_size: int = DEFAULT_CHUNK_SIZE
    ) -> int:
        """Calculate direct physical file offset for a given chunk index."""
        return HEADER_SIZE + chunk_index * (chunk_size + CHUNK_OVERHEAD)

    @classmethod
    def build_header(
        cls,
        plaintext_size: int,
        key_id: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        file_uuid: bytes | None = None,
        key_bytes: bytes | None = None,
    ) -> tuple[bytes, ChunkedContainerHeader]:
        """Construct and authenticate 84-byte binary container header."""
        if key_bytes is None:
            from core.crypto.service import EncryptionService

            _resolved_key_id, resolved_key_bytes = (
                EncryptionService._get_key_bytes(key_id)
            )
            key_bytes = resolved_key_bytes

        if file_uuid is None:
            file_uuid = uuid.uuid4().bytes
        elif len(file_uuid) != 16:
            raise ValueError("File UUID must be exactly 16 bytes")

        total_chunks = (
            math.ceil(plaintext_size / chunk_size) if plaintext_size > 0 else 0
        )
        key_id_bytes = key_id.encode("ascii").ljust(16, b"\x00")[:16]
        header_nonce = secrets.token_bytes(12)

        meta_bytes = struct.pack(
            ">8s16sIQI16s12s",
            MAGIC,
            key_id_bytes,
            chunk_size,
            plaintext_size,
            total_chunks,
            file_uuid,
            header_nonce,
        )

        aesgcm = AESGCM(key_bytes)
        cipher_with_tag = aesgcm.encrypt(header_nonce, b"", meta_bytes)
        header_tag = cipher_with_tag[-16:]

        full_header_bytes = meta_bytes + header_tag
        header_obj = ChunkedContainerHeader(
            magic=MAGIC,
            key_id=key_id,
            chunk_size=chunk_size,
            plaintext_size=plaintext_size,
            total_chunks=total_chunks,
            file_uuid=file_uuid,
            header_nonce=header_nonce,
            header_tag=header_tag,
        )
        return full_header_bytes, header_obj

    @classmethod
    def parse_header(
        cls,
        header_bytes: bytes,
        key_bytes: bytes | None = None,
    ) -> ChunkedContainerHeader:
        """Parse and verify 84-byte binary header with GMAC validation."""
        if len(header_bytes) < HEADER_SIZE:
            raise DecryptionIntegrityError(
                "Encrypted container header is truncated"
            )

        meta_bytes = header_bytes[:68]
        header_tag = header_bytes[68:84]

        try:
            (
                magic,
                raw_key_id,
                chunk_size,
                plaintext_size,
                total_chunks,
                file_uuid,
                header_nonce,
            ) = struct.unpack(">8s16sIQI16s12s", meta_bytes)
        except struct.error as err:
            raise DecryptionIntegrityError(
                "Failed to unpack container header"
            ) from err

        if magic != MAGIC:
            raise DecryptionIntegrityError(
                f"Invalid container magic: {magic!r}"
            )

        try:
            key_id = raw_key_id.rstrip(b"\x00").decode("ascii")
        except UnicodeDecodeError as err:
            raise DecryptionIntegrityError(
                "Corrupted container header key ID"
            ) from err

        if key_bytes is None:
            from core.crypto.service import EncryptionService

            _resolved_key_id, resolved_key_bytes = (
                EncryptionService._get_key_bytes(key_id)
            )
            key_bytes = resolved_key_bytes

        aesgcm = AESGCM(key_bytes)
        try:
            aesgcm.decrypt(header_nonce, header_tag, meta_bytes)
        except InvalidTag as err:
            raise DecryptionIntegrityError(
                "Header authentication tag validation failed"
            ) from err

        return ChunkedContainerHeader(
            magic=magic,
            key_id=key_id,
            chunk_size=chunk_size,
            plaintext_size=plaintext_size,
            total_chunks=total_chunks,
            file_uuid=file_uuid,
            header_nonce=header_nonce,
            header_tag=header_tag,
        )

    @classmethod
    def encrypt_chunk(
        cls,
        chunk_plaintext: bytes,
        chunk_index: int,
        file_uuid: bytes,
        key_bytes: bytes,
    ) -> bytes:
        """Encrypt single plaintext chunk with AES-256-GCM and bound AAD."""
        nonce = secrets.token_bytes(12)
        aad = CHUNK_AAD_PREFIX + file_uuid + chunk_index.to_bytes(4, "big")
        aesgcm = AESGCM(key_bytes)
        ciphertext_and_tag = aesgcm.encrypt(nonce, chunk_plaintext, aad)
        return nonce + ciphertext_and_tag

    @classmethod
    def decrypt_chunk(
        cls,
        chunk_cipher: bytes,
        chunk_index: int,
        file_uuid: bytes,
        key_bytes: bytes,
    ) -> bytes:
        """Decrypt single cipher chunk verifying AES-256-GCM tag with bound AAD."""
        if len(chunk_cipher) < CHUNK_OVERHEAD:
            raise DecryptionIntegrityError("Chunk ciphertext is truncated")

        nonce = chunk_cipher[:12]
        ciphertext_and_tag = chunk_cipher[12:]
        aad = CHUNK_AAD_PREFIX + file_uuid + chunk_index.to_bytes(4, "big")
        aesgcm = AESGCM(key_bytes)

        try:
            return aesgcm.decrypt(nonce, ciphertext_and_tag, aad)
        except InvalidTag as err:
            raise DecryptionIntegrityError(
                f"Chunk {chunk_index} authentication tag validation failed"
            ) from err
