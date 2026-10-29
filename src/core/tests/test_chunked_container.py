from __future__ import annotations

import os
import uuid

import pytest
from django.conf import settings

from core.crypto.container import (
    CHUNK_OVERHEAD,
    DEFAULT_CHUNK_SIZE,
    HEADER_SIZE,
    ChunkedContainerEngine,
    ChunkedContainerHeader,
)
from core.crypto.service import DecryptionIntegrityError


@pytest.fixture
def sample_key() -> bytes:
    return b"\x01" * 32


@pytest.fixture
def sample_uuid() -> bytes:
    return uuid.uuid4().bytes


def test_chunk_offset_calculation() -> None:
    assert ChunkedContainerEngine.get_chunk_offset(0, DEFAULT_CHUNK_SIZE) == HEADER_SIZE
    expected_chunk_1 = HEADER_SIZE + (DEFAULT_CHUNK_SIZE + CHUNK_OVERHEAD)
    assert (
        ChunkedContainerEngine.get_chunk_offset(1, DEFAULT_CHUNK_SIZE)
        == expected_chunk_1
    )
    expected_chunk_10 = HEADER_SIZE + 10 * (DEFAULT_CHUNK_SIZE + CHUNK_OVERHEAD)
    assert (
        ChunkedContainerEngine.get_chunk_offset(10, DEFAULT_CHUNK_SIZE)
        == expected_chunk_10
    )


def test_header_build_and_parse(sample_key: bytes, sample_uuid: bytes) -> None:
    key_id = "k1"
    plaintext_size = 2_500_000
    chunk_size = DEFAULT_CHUNK_SIZE

    header_bytes, parsed_header = ChunkedContainerEngine.build_header(
        plaintext_size=plaintext_size,
        key_id=key_id,
        chunk_size=chunk_size,
        file_uuid=sample_uuid,
        key_bytes=sample_key,
    )

    assert len(header_bytes) == HEADER_SIZE
    assert parsed_header.magic == b"LFENC02\x00"
    assert parsed_header.key_id == "k1"
    assert parsed_header.chunk_size == chunk_size
    assert parsed_header.plaintext_size == plaintext_size
    assert parsed_header.total_chunks == 3
    assert parsed_header.file_uuid == sample_uuid
    assert len(parsed_header.header_nonce) == 12
    assert len(parsed_header.header_tag) == 16

    deserialized = ChunkedContainerEngine.parse_header(
        header_bytes, key_bytes=sample_key
    )
    assert deserialized.magic == parsed_header.magic
    assert deserialized.key_id == "k1"
    assert deserialized.chunk_size == chunk_size
    assert deserialized.plaintext_size == plaintext_size
    assert deserialized.total_chunks == 3
    assert deserialized.file_uuid == sample_uuid


def test_header_tampering_fails_integrity(
    sample_key: bytes, sample_uuid: bytes
) -> None:
    header_bytes, _ = ChunkedContainerEngine.build_header(
        plaintext_size=1024,
        key_id="k1",
        chunk_size=DEFAULT_CHUNK_SIZE,
        file_uuid=sample_uuid,
        key_bytes=sample_key,
    )

    tampered_bytes = bytearray(header_bytes)
    tampered_bytes[20] ^= 0xFF

    with pytest.raises(DecryptionIntegrityError):
        ChunkedContainerEngine.parse_header(bytes(tampered_bytes), key_bytes=sample_key)


def test_header_truncated_fails(sample_key: bytes) -> None:
    with pytest.raises(DecryptionIntegrityError):
        ChunkedContainerEngine.parse_header(
            b"LFENC02\x00" + b"\x00" * 20, key_bytes=sample_key
        )


def test_chunk_encryption_and_decryption(sample_key: bytes, sample_uuid: bytes) -> None:
    plaintext = b"Test payload for encrypted chunk 0"
    chunk_index = 0

    chunk_cipher = ChunkedContainerEngine.encrypt_chunk(
        chunk_plaintext=plaintext,
        chunk_index=chunk_index,
        file_uuid=sample_uuid,
        key_bytes=sample_key,
    )

    assert len(chunk_cipher) == 12 + len(plaintext) + 16

    decrypted = ChunkedContainerEngine.decrypt_chunk(
        chunk_cipher=chunk_cipher,
        chunk_index=chunk_index,
        file_uuid=sample_uuid,
        key_bytes=sample_key,
    )
    assert decrypted == plaintext


def test_chunk_tamper_detection(sample_key: bytes, sample_uuid: bytes) -> None:
    plaintext = b"Tamper test chunk"
    chunk_cipher = ChunkedContainerEngine.encrypt_chunk(
        chunk_plaintext=plaintext,
        chunk_index=1,
        file_uuid=sample_uuid,
        key_bytes=sample_key,
    )

    tampered_cipher = bytearray(chunk_cipher)
    tampered_cipher[15] ^= 0x01

    with pytest.raises(DecryptionIntegrityError):
        ChunkedContainerEngine.decrypt_chunk(
            chunk_cipher=bytes(tampered_cipher),
            chunk_index=1,
            file_uuid=sample_uuid,
            key_bytes=sample_key,
        )


def test_chunk_aad_mismatch_fails(sample_key: bytes, sample_uuid: bytes) -> None:
    plaintext = b"AAD mismatch test"
    chunk_cipher = ChunkedContainerEngine.encrypt_chunk(
        chunk_plaintext=plaintext,
        chunk_index=0,
        file_uuid=sample_uuid,
        key_bytes=sample_key,
    )

    with pytest.raises(DecryptionIntegrityError):
        ChunkedContainerEngine.decrypt_chunk(
            chunk_cipher=chunk_cipher,
            chunk_index=1,
            file_uuid=sample_uuid,
            key_bytes=sample_key,
        )

    different_uuid = uuid.uuid4().bytes
    with pytest.raises(DecryptionIntegrityError):
        ChunkedContainerEngine.decrypt_chunk(
            chunk_cipher=chunk_cipher,
            chunk_index=0,
            file_uuid=different_uuid,
            key_bytes=sample_key,
        )
