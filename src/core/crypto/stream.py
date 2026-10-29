"""Seekable virtual stream reader for LFENC02 chunked encrypted files."""

from __future__ import annotations

import io
from collections.abc import Buffer
from typing import BinaryIO

from core.crypto.container import (
    CHUNK_OVERHEAD,
    HEADER_SIZE,
    ChunkedContainerEngine,
    ChunkedContainerHeader,
)
from core.crypto.service import EncryptionService


class EncryptedStreamReader(io.RawIOBase):
    """Seekable read-only stream decrypting LFENC02 chunks on demand."""

    def __init__(
        self,
        raw_file: BinaryIO,
        key_bytes: bytes | None = None,
    ) -> None:
        """Initialize stream reader, parsing container header."""
        self._raw_file = raw_file
        self._raw_file.seek(0)
        header_bytes = self._raw_file.read(HEADER_SIZE)

        self._header: ChunkedContainerHeader = (
            ChunkedContainerEngine.parse_header(
                header_bytes,
                key_bytes=key_bytes,
            )
        )

        if key_bytes is None:
            _key_id, resolved_key_bytes = EncryptionService._get_key_bytes(
                self._header.key_id
            )
            self._key_bytes = resolved_key_bytes
        else:
            self._key_bytes = key_bytes

        self._cursor: int = 0
        self._last_chunk_index: int | None = None
        self._last_chunk_data: bytes | None = None
        self._closed: bool = False

    @property
    def size(self) -> int:
        """Return total unencrypted plaintext size in bytes."""
        return self._header.plaintext_size

    @property
    def header(self) -> ChunkedContainerHeader:
        """Return parsed container header."""
        return self._header

    def readable(self) -> bool:
        """Return True if stream is open and readable."""
        return not self._closed

    def seekable(self) -> bool:
        """Return True if stream supports random-access seeking."""
        return not self._closed

    def writable(self) -> bool:
        """Return False because stream reader is strictly read-only."""
        return False

    def tell(self) -> int:
        """Return current virtual cursor position."""
        self._check_closed()
        return self._cursor

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        """Seek virtual cursor to specific position."""
        self._check_closed()
        match whence:
            case io.SEEK_SET:
                target = offset
            case io.SEEK_CUR:
                target = self._cursor + offset
            case io.SEEK_END:
                target = self._header.plaintext_size + offset
            case _:
                raise ValueError(f"Invalid whence argument: {whence}")

        self._cursor = max(0, min(target, self._header.plaintext_size))
        return self._cursor

    def read(self, size: int = -1) -> bytes:
        """Read and decrypt specified bytes spanning chunk boundaries."""
        self._check_closed()
        if self._cursor >= self._header.plaintext_size:
            return b""

        if size < 0:
            to_read = self._header.plaintext_size - self._cursor
        else:
            to_read = min(size, self._header.plaintext_size - self._cursor)

        if to_read <= 0:
            return b""

        start_chunk = self._cursor // self._header.chunk_size
        end_chunk = (self._cursor + to_read - 1) // self._header.chunk_size

        output = bytearray()
        for chunk_idx in range(start_chunk, end_chunk + 1):
            chunk_plain = self._get_chunk_plaintext(chunk_idx)
            chunk_base_offset = chunk_idx * self._header.chunk_size
            slice_start = max(0, self._cursor - chunk_base_offset)
            slice_end = min(
                len(chunk_plain),
                self._cursor + to_read - chunk_base_offset,
            )
            output.extend(chunk_plain[slice_start:slice_end])

        self._cursor += to_read
        return bytes(output)

    def readinto(self, b: Buffer) -> int:
        """Read bytes into a pre-allocated writable bytes-like object b."""
        data = self.read(len(b))  # type: ignore[arg-type]
        n = len(data)
        b[:n] = data  # type: ignore[index]
        return n

    def _get_chunk_plaintext(self, chunk_index: int) -> bytes:
        if (
            self._last_chunk_index == chunk_index
            and self._last_chunk_data is not None
        ):
            return self._last_chunk_data

        physical_offset = ChunkedContainerEngine.get_chunk_offset(
            chunk_index, self._header.chunk_size
        )
        self._raw_file.seek(physical_offset)

        if chunk_index < self._header.total_chunks - 1:
            plain_len = self._header.chunk_size
        else:
            plain_len = self._header.plaintext_size - (
                chunk_index * self._header.chunk_size
            )

        cipher_len = plain_len + CHUNK_OVERHEAD
        chunk_cipher = self._raw_file.read(cipher_len)

        decrypted = ChunkedContainerEngine.decrypt_chunk(
            chunk_cipher=chunk_cipher,
            chunk_index=chunk_index,
            file_uuid=self._header.file_uuid,
            key_bytes=self._key_bytes,
        )

        self._last_chunk_index = chunk_index
        self._last_chunk_data = decrypted
        return decrypted

    def _check_closed(self) -> None:
        if self._closed:
            raise ValueError("I/O operation on closed EncryptedStreamReader")

    def close(self) -> None:
        """Close underlying file descriptor and clear cached buffers."""
        if not self._closed:
            self._closed = True
            self._last_chunk_data = None
            try:
                self._raw_file.close()
            finally:
                super().close()
