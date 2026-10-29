"""Tests for bounded-memory FileValidator and extension-MIME verification."""

from __future__ import annotations

import io

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from core.utils.file_upload_validator import FileValidator


@pytest.mark.unit
def test_file_validator_detects_spoofed_extension() -> None:
    """Verify that a script disguised with a .pdf extension is rejected."""
    validator = FileValidator(
        max_size=1024 * 1024,
        content_types=("application/pdf",),
    )
    fake_pdf = SimpleUploadedFile("invoice.pdf", b"#!/bin/bash\necho 'pwned'\n")
    with pytest.raises(ValidationError) as exc:
        validator(fake_pdf)
    msg = str(exc.value)
    assert "Files of type" in msg or "extension" in msg


@pytest.mark.unit
def test_file_validator_bounded_memory_read_and_rewind() -> None:
    """Verify that validator reads at most 4096 bytes and rewinds stream pointer."""

    class TrackingStream(io.BytesIO):
        def __init__(self, initial_bytes: bytes) -> None:
            super().__init__(initial_bytes)
            self.max_read_amount = 0
            self.size = len(initial_bytes)
            self.name = "document.pdf"

        def read(self, size: int = -1) -> bytes:
            if size > self.max_read_amount:
                self.max_read_amount = size
            return super().read(size)

    stream = TrackingStream(b"%PDF-1.4\n" + b"0" * 10000)
    validator = FileValidator(
        max_size=20000,
        content_types=("application/pdf",),
    )
    validator(stream)
    assert stream.max_read_amount <= 4096
    assert stream.tell() == 0


@pytest.mark.unit
def test_file_validator_rejects_oversized_file() -> None:
    """Verify max_size limit enforcement."""
    validator = FileValidator(max_size=1000)
    file_obj = SimpleUploadedFile("test.pdf", b"%PDF-1.4\n" + b"A" * 1500)
    with pytest.raises(ValidationError) as exc:
        validator(file_obj)
    assert "Ensure this file size is not greater than" in str(exc.value)


@pytest.mark.unit
def test_file_validator_rejects_undersized_file() -> None:
    """Verify min_size limit enforcement."""
    validator = FileValidator(min_size=50)
    file_obj = SimpleUploadedFile("test.pdf", b"%PDF-1.4\n")
    with pytest.raises(ValidationError) as exc:
        validator(file_obj)
    assert "Ensure this file size is not less than" in str(exc.value)


@pytest.mark.unit
def test_file_validator_unnamed_stream_skips_extension_check() -> None:
    """Verify stream without a name still validates MIME without crashing."""
    stream = io.BytesIO(b"%PDF-1.4\nvalid pdf header stream")
    stream.size = len(stream.getvalue())
    validator = FileValidator(
        max_size=10000,
        content_types=("application/pdf",),
    )
    # Should pass without AttributeError on name
    validator(stream)
    assert stream.tell() == 0


@pytest.mark.unit
def test_file_validator_extension_not_matching_mime() -> None:
    """Verify that a valid PDF renamed to .png is rejected."""
    # Real PDF header but named invoice.png
    fake_png = SimpleUploadedFile("invoice.png", b"%PDF-1.4\nPDF header")
    validator = FileValidator(
        max_size=1024 * 1024,
        content_types=("application/pdf", "image/png"),
    )
    with pytest.raises(ValidationError) as exc:
        validator(fake_png)
    assert "extension" in str(exc.value).lower() or "not supported" in str(exc.value).lower()


@pytest.mark.unit
def test_file_validator_rejects_unmapped_extension() -> None:
    """Verify that an unmapped extension (e.g. .sh or .exe) is rejected even if MIME matches."""
    validator = FileValidator(
        max_size=1024 * 1024,
        content_types=("text/plain",),
    )
    fake_script = SimpleUploadedFile("deploy.sh", b"Hello plain text world\n")
    with pytest.raises(ValidationError) as exc:
        validator(fake_script)
    assert "extension '.sh' is not supported" in str(exc.value).lower()


@pytest.mark.unit
def test_file_validator_rejects_empty_file() -> None:
    """Verify that a zero-byte upload is rejected."""
    validator = FileValidator(
        max_size=1024 * 1024,
        content_types=("application/pdf",),
    )
    empty_file = SimpleUploadedFile("empty.pdf", b"")
    with pytest.raises(ValidationError) as exc:
        validator(empty_file)
    assert "not supported" in str(exc.value).lower() or "empty" in str(exc.value).lower()


@pytest.mark.unit
def test_file_validator_seeks_to_start_before_reading() -> None:
    """Verify stream is rewound to 0 before reading header even if offset is non-zero."""
    stream = io.BytesIO(b"%PDF-1.4\nvalid content")
    stream.seek(4)
    stream.size = len(stream.getvalue())
    stream.name = "doc.pdf"
    validator = FileValidator(
        max_size=10000,
        content_types=("application/pdf",),
    )
    validator(stream)
    assert stream.tell() == 0
