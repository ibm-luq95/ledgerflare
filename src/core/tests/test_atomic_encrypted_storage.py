from __future__ import annotations

import io
from pathlib import Path

import pytest
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import FileSystemStorage

from core.crypto.container import MAGIC as MAGIC_V2
from core.crypto.service import EncryptionService
from core.storage.encrypted_storage import EncryptedPrivateStorage


@pytest.fixture
def temp_storage(tmp_path: Path) -> EncryptedPrivateStorage:
    return EncryptedPrivateStorage(location=str(tmp_path))


def test_save_and_open_roundtrip(temp_storage: EncryptedPrivateStorage) -> None:
    content = b"Confidential financial statement data for client ABC."
    saved_name = temp_storage.save("statements/client_abc.txt", ContentFile(content))

    disk_path = Path(temp_storage.path(saved_name))
    assert disk_path.exists()

    raw_on_disk = disk_path.read_bytes()
    assert raw_on_disk.startswith(MAGIC_V2)

    with temp_storage.open(saved_name, "rb") as opened_file:
        read_content = opened_file.read()
    assert read_content == content


def test_chunked_streaming_for_large_file(
    temp_storage: EncryptedPrivateStorage,
) -> None:
    # 2.5 MB content
    large_content = b"X" * (2_500_000)
    saved_name = temp_storage.save("large_doc.bin", ContentFile(large_content))

    with temp_storage.open(saved_name, "rb") as opened_file:
        # Seek and partial read
        opened_file.seek(1_500_000)
        chunk = opened_file.read(100)
        assert chunk == b"X" * 100

        opened_file.seek(0)
        full = opened_file.read()
        assert len(full) == len(large_content)
        assert full == large_content


def test_aborted_upload_cleans_up_staging_file(
    temp_storage: EncryptedPrivateStorage,
) -> None:
    class FailingStream(io.BytesIO):
        def __init__(self, data: bytes) -> None:
            super().__init__(data)
            self._calls = 0

        def read(self, size: int = -1) -> bytes:
            self._calls += 1
            if self._calls > 1:
                raise OSError("Network connection lost during upload")
            return super().read(size)

    failing_content = FailingStream(b"Initial chunk" * 100_000)
    target_name = "reports/aborted.pdf"

    with pytest.raises(OSError, match="Network connection lost"):
        temp_storage.save(target_name, failing_content)

    final_path = Path(temp_storage.path(target_name))
    assert not final_path.exists()

    staging_dir = final_path.parent
    if staging_dir.exists():
        tmp_files = list(staging_dir.glob(".tmp.*"))
        assert len(tmp_files) == 0


def test_backward_compatibility_unencrypted_file(
    temp_storage: EncryptedPrivateStorage,
) -> None:
    plaintext_data = b"%PDF-1.4 raw production unencrypted document"
    filename = "legacy_unencrypted.pdf"
    disk_path = Path(temp_storage.path(filename))
    disk_path.parent.mkdir(parents=True, exist_ok=True)
    disk_path.write_bytes(plaintext_data)

    with temp_storage.open(filename, "rb") as opened_file:
        data = opened_file.read()
    assert data == plaintext_data


def test_backward_compatibility_legacy_v1_single_blob(
    temp_storage: EncryptedPrivateStorage,
) -> None:
    secret_text = b"Legacy single blob encrypted data"
    filename = "legacy_v1.txt"
    aad = f"Storage:{filename}".encode()
    v1_ciphertext = EncryptionService.encrypt_bytes(secret_text, aad)

    disk_path = Path(temp_storage.path(filename))
    disk_path.parent.mkdir(parents=True, exist_ok=True)
    disk_path.write_bytes(v1_ciphertext)

    with temp_storage.open(filename, "rb") as opened_file:
        data = opened_file.read()
    assert data == secret_text


def test_simple_uploaded_file_chunking_integrity(
    temp_storage: EncryptedPrivateStorage,
) -> None:
    uploaded_data = b"U" * 2_000_000
    uploaded_file = SimpleUploadedFile("statement.bin", uploaded_data)
    saved_name = temp_storage.save("uploads/statement.bin", uploaded_file)

    with temp_storage.open(saved_name, "rb") as opened_file:
        read_back = opened_file.read()
    assert read_back == uploaded_data
