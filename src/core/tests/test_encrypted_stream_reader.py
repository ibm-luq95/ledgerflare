from __future__ import annotations

import io
import uuid

import pytest

from core.crypto.container import (
    DEFAULT_CHUNK_SIZE,
    HEADER_SIZE,
    ChunkedContainerEngine,
)
from core.crypto.service import DecryptionIntegrityError
from core.crypto.stream import EncryptedStreamReader


@pytest.fixture
def sample_key() -> bytes:
    return b"\x02" * 32


@pytest.fixture
def encrypted_multi_chunk_file(sample_key: bytes) -> tuple[io.BytesIO, bytes]:
    chunk_size = 100
    file_uuid = uuid.uuid4().bytes
    p1 = b"A" * 100
    p2 = b"B" * 100
    p3 = b"C" * 50
    full_plaintext = p1 + p2 + p3

    header_bytes, _ = ChunkedContainerEngine.build_header(
        plaintext_size=len(full_plaintext),
        key_id="k1",
        chunk_size=chunk_size,
        file_uuid=file_uuid,
        key_bytes=sample_key,
    )

    c0 = ChunkedContainerEngine.encrypt_chunk(p1, 0, file_uuid, sample_key)
    c1 = ChunkedContainerEngine.encrypt_chunk(p2, 1, file_uuid, sample_key)
    c2 = ChunkedContainerEngine.encrypt_chunk(p3, 2, file_uuid, sample_key)

    raw_stream = io.BytesIO(header_bytes + c0 + c1 + c2)
    return raw_stream, full_plaintext


def test_reader_properties(
    encrypted_multi_chunk_file: tuple[io.BytesIO, bytes], sample_key: bytes
) -> None:
    raw_stream, full_plaintext = encrypted_multi_chunk_file
    reader = EncryptedStreamReader(raw_stream, key_bytes=sample_key)

    assert reader.readable() is True
    assert reader.seekable() is True
    assert reader.writable() is False
    assert reader.size == len(full_plaintext)
    assert reader.tell() == 0


def test_reader_sequential_read(
    encrypted_multi_chunk_file: tuple[io.BytesIO, bytes], sample_key: bytes
) -> None:
    raw_stream, full_plaintext = encrypted_multi_chunk_file
    reader = EncryptedStreamReader(raw_stream, key_bytes=sample_key)

    data = reader.read()
    assert data == full_plaintext
    assert reader.tell() == len(full_plaintext)

    # Next read returns EOF
    assert reader.read() == b""


def test_reader_chunk_boundary_span_read(
    encrypted_multi_chunk_file: tuple[io.BytesIO, bytes], sample_key: bytes
) -> None:
    raw_stream, full_plaintext = encrypted_multi_chunk_file
    reader = EncryptedStreamReader(raw_stream, key_bytes=sample_key)

    # Offset 90 to 110 spans Chunk 0 (bytes 90-99 = 'A' * 10) and Chunk 1 (bytes 100-109 = 'B' * 10)
    reader.seek(90)
    assert reader.tell() == 90
    slice_data = reader.read(20)
    assert slice_data == (b"A" * 10) + (b"B" * 10)
    assert reader.tell() == 110


def test_reader_direct_seek_random_access(
    encrypted_multi_chunk_file: tuple[io.BytesIO, bytes], sample_key: bytes
) -> None:
    raw_stream, full_plaintext = encrypted_multi_chunk_file
    reader = EncryptedStreamReader(raw_stream, key_bytes=sample_key)

    # Seek directly to chunk 2 (offset 210)
    reader.seek(210, io.SEEK_SET)
    assert reader.tell() == 210
    chunk2_slice = reader.read(10)
    assert chunk2_slice == b"C" * 10
    assert reader.tell() == 220


def test_reader_seek_whence_modes(
    encrypted_multi_chunk_file: tuple[io.BytesIO, bytes], sample_key: bytes
) -> None:
    raw_stream, full_plaintext = encrypted_multi_chunk_file
    reader = EncryptedStreamReader(raw_stream, key_bytes=sample_key)

    # SEEK_END
    pos = reader.seek(-10, io.SEEK_END)
    assert pos == len(full_plaintext) - 10
    assert reader.read(10) == b"C" * 10

    # SEEK_CUR
    reader.seek(50, io.SEEK_SET)
    reader.seek(20, io.SEEK_CUR)
    assert reader.tell() == 70

    # Out of bounds clamping
    reader.seek(-50, io.SEEK_SET)
    assert reader.tell() == 0

    reader.seek(999999, io.SEEK_SET)
    assert reader.tell() == len(full_plaintext)


def test_reader_corrupted_chunk_fails(
    encrypted_multi_chunk_file: tuple[io.BytesIO, bytes], sample_key: bytes
) -> None:
    raw_stream, _ = encrypted_multi_chunk_file
    buffer_bytes = bytearray(raw_stream.getvalue())

    # Tamper with chunk 1 (starts after header + chunk 0)
    # chunk 0 length = 12 + 100 + 16 = 128
    # header = 84
    # chunk 1 starts at 84 + 128 = 212
    tampered_offset = 212 + 20
    buffer_bytes[tampered_offset] ^= 0x01

    tampered_stream = io.BytesIO(bytes(buffer_bytes))
    reader = EncryptedStreamReader(tampered_stream, key_bytes=sample_key)

    # Chunk 0 reads fine
    assert reader.read(50) == b"A" * 50

    # Reading into chunk 1 raises DecryptionIntegrityError
    reader.seek(105)
    with pytest.raises(DecryptionIntegrityError):
        reader.read(10)


def test_reader_readinto(
    encrypted_multi_chunk_file: tuple[io.BytesIO, bytes], sample_key: bytes
) -> None:
    raw_stream, full_plaintext = encrypted_multi_chunk_file
    reader = EncryptedStreamReader(raw_stream, key_bytes=sample_key)

    buf = bytearray(50)
    n = reader.readinto(buf)
    assert n == 50
    assert bytes(buf) == full_plaintext[:50]
    assert reader.tell() == 50
