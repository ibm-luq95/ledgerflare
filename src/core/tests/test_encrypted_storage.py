from __future__ import annotations

from pathlib import Path

import pytest
from django.core.files.base import ContentFile

from core.crypto.service import DecryptionIntegrityError
from core.storage.encrypted_storage import EncryptedPrivateStorage


@pytest.mark.unit
def test_encrypted_storage_roundtrip(tmp_path: Path) -> None:
    storage = EncryptedPrivateStorage(location=str(tmp_path))
    content = b"PDF Confidential Financial Statements 2026"
    saved_name = storage.save("reports/statement.pdf", ContentFile(content))

    with storage.open(saved_name, "rb") as f:
        read_back = f.read()
    assert read_back == content

    raw_disk_path = Path(storage.path(saved_name))
    with raw_disk_path.open("rb") as raw_f:
        disk_bytes = raw_f.read()
    assert disk_bytes.startswith(b"LFENC02\x00")
    assert b"Confidential" not in disk_bytes


@pytest.mark.unit
def test_encrypted_storage_tamper_fails(tmp_path: Path) -> None:
    storage = EncryptedPrivateStorage(location=str(tmp_path))
    saved_name = storage.save("tamper.bin", ContentFile(b"Real Data"))
    raw_path = Path(storage.path(saved_name))

    with raw_path.open("rb") as f:
        data = bytearray(f.read())
    data[-5] ^= 0xFF
    with raw_path.open("wb") as f:
        f.write(data)

    with (
        pytest.raises(DecryptionIntegrityError),
        storage.open(saved_name, "rb") as f,
    ):
        _ = f.read()


@pytest.mark.unit
def test_encrypted_storage_empty_file(tmp_path: Path) -> None:
    storage = EncryptedPrivateStorage(location=str(tmp_path))
    saved_name = storage.save("empty.txt", ContentFile(b""))

    with storage.open(saved_name, "rb") as f:
        assert f.read() == b""


@pytest.mark.unit
def test_encrypted_storage_large_file_chunking(tmp_path: Path) -> None:
    storage = EncryptedPrivateStorage(location=str(tmp_path))
    # 256KB payload
    large_content = b"CHUNK_DATA_12345" * 16384
    saved_name = storage.save("large_doc.bin", ContentFile(large_content))

    with storage.open(saved_name, "rb") as f:
        read_back = f.read()
    assert read_back == large_content


@pytest.mark.unit
def test_encrypted_storage_truncated_header_raises(tmp_path: Path) -> None:
    storage = EncryptedPrivateStorage(location=str(tmp_path))
    saved_name = storage.save("truncated.bin", ContentFile(b"Hello World"))
    raw_path = Path(storage.path(saved_name))

    # Truncate file to just 5 bytes (smaller than header + nonce + tag)
    with raw_path.open("wb") as f:
        f.write(b"LFENC")

    with (
        pytest.raises(DecryptionIntegrityError),
        storage.open(saved_name, "rb") as f,
    ):
        _ = f.read()


@pytest.mark.unit
def test_encrypted_storage_invalid_magic_header_raises(tmp_path: Path) -> None:
    storage = EncryptedPrivateStorage(location=str(tmp_path))
    saved_name = storage.save("bad_header.bin", ContentFile(b"Secure Document"))
    raw_path = Path(storage.path(saved_name))

    with raw_path.open("rb") as f:
        data = bytearray(f.read())
    # Corrupt magic header with unknown LFENC version
    data[0:8] = b"LFENC99\x00"
    with raw_path.open("wb") as f:
        f.write(data)

    with (
        pytest.raises(DecryptionIntegrityError),
        storage.open(saved_name, "rb") as f,
    ):
        _ = f.read()


@pytest.mark.unit
def test_encrypted_storage_text_mode(tmp_path: Path) -> None:
    storage = EncryptedPrivateStorage(location=str(tmp_path))
    text_content = "Confidential Financial Ledger Entry\nSecond Line\n"
    saved_name = storage.save("notes.txt", ContentFile(text_content.encode("utf-8")))

    with storage.open(saved_name, "rt") as f:
        lines = f.readlines()
    assert lines == ["Confidential Financial Ledger Entry\n", "Second Line\n"]


@pytest.mark.unit
def test_encrypted_storage_deconstruct() -> None:
    storage = EncryptedPrivateStorage(location="/custom/storage")
    path, args, kwargs = storage.deconstruct()
    assert path == "core.storage.encrypted_storage.EncryptedPrivateStorage"
    assert isinstance(args, list)
    assert isinstance(kwargs, dict)
