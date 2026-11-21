"""Encrypted private storage backend with zero-corruption atomic staging."""

from __future__ import annotations

import contextlib
import io
import logging
import os
import struct
import tempfile
import uuid
from pathlib import Path
from typing import Any

from django.core.files.base import File
from django.core.files.storage import FileSystemStorage

from core.crypto.container import (
    DEFAULT_CHUNK_SIZE,
    ChunkedContainerEngine,
)
from core.crypto.container import (
    MAGIC as MAGIC_V2,
)
from core.crypto.service import DecryptionIntegrityError, EncryptionService
from core.crypto.stream import EncryptedStreamReader


logger = logging.getLogger(__name__)


class EncryptedPrivateStorage(FileSystemStorage):
    """Storage backend encrypting file streams with AES-256-GCM chunking."""

    def _save(self, name: str, content: File[Any]) -> str:
        final_disk_path = Path(self.path(name))
        target_dir = final_disk_path.parent
        target_dir.mkdir(parents=True, exist_ok=True)

        staging_path = target_dir / f".tmp.{uuid.uuid4().hex}.upload"

        key_id, key_bytes = EncryptionService._get_key_bytes()
        file_uuid = uuid.uuid4().bytes

        plaintext_size, content = self._prepare_content_and_size(content)
        header_bytes, _ = ChunkedContainerEngine.build_header(
            plaintext_size=plaintext_size,
            key_id=key_id,
            chunk_size=DEFAULT_CHUNK_SIZE,
            file_uuid=file_uuid,
            key_bytes=key_bytes,
        )

        staging_file = None
        try:
            staging_file = staging_path.open("wb")
            staging_file.write(header_bytes)

            chunk_index = 0
            if hasattr(content, "read"):
                if hasattr(content, "seek"):
                    with contextlib.suppress(
                        AttributeError, io.UnsupportedOperation, OSError
                    ):
                        content.seek(0)
                while True:
                    chunk = content.read(DEFAULT_CHUNK_SIZE)
                    if not chunk:
                        break
                    chunk_bytes = (
                        chunk
                        if isinstance(chunk, bytes)
                        else chunk.encode("utf-8")
                    )
                    cipher_chunk = ChunkedContainerEngine.encrypt_chunk(
                        chunk_plaintext=chunk_bytes,
                        chunk_index=chunk_index,
                        file_uuid=file_uuid,
                        key_bytes=key_bytes,
                    )
                    staging_file.write(cipher_chunk)
                    chunk_index += 1
            elif hasattr(content, "chunks"):
                for raw_chunk in content.chunks(chunk_size=DEFAULT_CHUNK_SIZE):
                    chunk_bytes = (
                        raw_chunk
                        if isinstance(raw_chunk, bytes)
                        else raw_chunk.encode("utf-8")
                    )
                    for i in range(0, len(chunk_bytes), DEFAULT_CHUNK_SIZE):
                        slice_bytes = chunk_bytes[i : i + DEFAULT_CHUNK_SIZE]
                        cipher_chunk = ChunkedContainerEngine.encrypt_chunk(
                            chunk_plaintext=slice_bytes,
                            chunk_index=chunk_index,
                            file_uuid=file_uuid,
                            key_bytes=key_bytes,
                        )
                        staging_file.write(cipher_chunk)
                        chunk_index += 1

            staging_file.flush()
            os.fsync(staging_file.fileno())
            staging_file.close()
            staging_file = None

            staging_path.replace(final_disk_path)
            return name

        except Exception:
            if staging_file is not None and not staging_file.closed:
                staging_file.close()
            if staging_path.exists():
                staging_path.unlink(missing_ok=True)
            logger.exception("Storage upload aborted for %s", name)
            raise

    def _open(self, name: str, mode: str = "rb") -> File[Any]:
        underlying = super()._open(name, "rb")  # type: ignore[misc]
        magic = underlying.read(8)
        underlying.seek(0)

        if magic == MAGIC_V2:
            stream_reader = EncryptedStreamReader(underlying.file)
            file_obj: File[Any] = File(stream_reader, name=name)  # type: ignore[arg-type]
            file_obj.size = stream_reader.size
        elif magic.startswith(b"LFENC01"):
            encrypted_bytes = underlying.read()
            underlying.close()
            aad = f"Storage:{name}".encode()
            decrypted_bytes = EncryptionService.decrypt_bytes(
                encrypted_bytes, aad
            )
            buf = io.BytesIO(decrypted_bytes)
            file_obj = File(buf, name=name)
        elif magic.startswith(b"LFENC"):
            underlying.close()
            raise DecryptionIntegrityError(
                "Truncated or unrecognized encrypted container header"
            )
        else:
            file_obj = File(underlying, name=name)

        if "t" in mode:
            return io.TextIOWrapper(file_obj)  # type: ignore[return-value]
        return file_obj

    def _prepare_content_and_size(
        self, content: File[Any]
    ) -> tuple[int, File[Any]]:
        if hasattr(content, "size") and isinstance(content.size, int):
            return content.size, content

        if hasattr(content, "seek") and hasattr(content, "tell"):
            current_pos = content.tell()
            content.seek(0, os.SEEK_END)
            size = content.tell()
            content.seek(current_pos)
            return size, content

        spool = tempfile.SpooledTemporaryFile(max_size=5 * 1024 * 1024)
        if hasattr(content, "read"):
            while True:
                buf = content.read(DEFAULT_CHUNK_SIZE)
                if not buf:
                    break
                spool.write(
                    buf if isinstance(buf, bytes) else buf.encode("utf-8")
                )
        elif hasattr(content, "chunks"):
            for chunk in content.chunks():
                spool.write(
                    chunk if isinstance(chunk, bytes) else chunk.encode("utf-8")
                )
        spool.seek(0, os.SEEK_END)
        size = spool.tell()
        spool.seek(0)
        return size, File(spool)

    def size(self, name: str) -> int:
        """Return logical plaintext size in bytes from container header."""
        full_path = Path(self.path(name))
        try:
            with full_path.open("rb") as f:
                magic = f.read(8)
                if magic == MAGIC_V2:
                    f.seek(28)
                    (plaintext_size,) = struct.unpack(">Q", f.read(8))
                    return plaintext_size
        except (OSError, struct.error):
            pass
        return super().size(name)

    def deconstruct(self) -> tuple[str, list[Any], dict[str, Any]]:
        """Deconstruct storage class for Django migration serialization."""
        _path, args, kwargs = super().deconstruct()
        return (
            "core.storage.encrypted_storage.EncryptedPrivateStorage",
            list(args),
            kwargs,
        )
