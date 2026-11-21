"""Tests for hardened file upload validation in DocumentForm and DocumentSerializer."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.fields.files import FieldFile
from rest_framework.exceptions import ValidationError as DRFValidationError

from document.forms import DocumentForm
from document.serializers import DocumentSerializer


@pytest.mark.unit
def test_document_form_rejects_oversized_file() -> None:
    """Verify DocumentForm rejects uploads exceeding MAX_DOCUMENT_UPLOAD_SIZE."""
    form = DocumentForm()
    max_size = settings.MAX_DOCUMENT_UPLOAD_SIZE
    large_file = SimpleUploadedFile("large.pdf", b"%PDF-1.4\n" + b"A" * 100)
    large_file.size = max_size + 1
    form.cleaned_data = {"document_file": large_file}

    with pytest.raises(DjangoValidationError) as exc:
        form.clean_document_file()
    assert "Ensure this file size is not greater than" in str(exc.value)


@pytest.mark.unit
def test_document_form_rejects_spoofed_file() -> None:
    """Verify DocumentForm rejects spoofed script disguised as a PDF."""
    form = DocumentForm()
    spoofed = SimpleUploadedFile("script.pdf", b"#!/bin/bash\nrm -rf /")
    form.cleaned_data = {"document_file": spoofed}

    with pytest.raises(DjangoValidationError) as exc:
        form.clean_document_file()
    assert "Files of type" in str(exc.value) or "extension" in str(exc.value)


@pytest.mark.unit
def test_document_form_accepts_valid_pdf() -> None:
    """Verify DocumentForm accepts a legitimate PDF payload."""
    form = DocumentForm()
    valid_pdf = SimpleUploadedFile("valid.pdf", b"%PDF-1.4\n1 0 obj\n<<>>\nendobj")
    form.cleaned_data = {"document_file": valid_pdf}
    result = form.clean_document_file()
    assert result == valid_pdf


@pytest.mark.unit
def test_document_form_skips_validation_for_existing_file() -> None:
    """Verify DocumentForm skips re-validation for existing on-disk FieldFile."""
    form = DocumentForm(is_update=True)
    existing_field_file = MagicMock(spec=FieldFile)
    form.cleaned_data = {"document_file": existing_field_file}
    result = form.clean_document_file()
    assert result == existing_field_file


@pytest.mark.unit
def test_document_serializer_rejects_oversized_file() -> None:
    """Verify DocumentSerializer rejects files exceeding MAX_DOCUMENT_UPLOAD_SIZE."""
    serializer = DocumentSerializer()
    max_size = settings.MAX_DOCUMENT_UPLOAD_SIZE
    large_file = SimpleUploadedFile("large.pdf", b"%PDF-1.4\n" + b"B" * 100)
    large_file.size = max_size + 1

    with pytest.raises(DRFValidationError) as exc:
        serializer.validate_document_file(large_file)
    assert "Ensure this file size is not greater than" in str(exc.value)


@pytest.mark.unit
def test_document_serializer_rejects_spoofed_file() -> None:
    """Verify DocumentSerializer rejects spoofed executable payload."""
    serializer = DocumentSerializer()
    spoofed = SimpleUploadedFile("calc.pdf", b"MZ\x90\x00\x03\x00\x00\x00")
    with pytest.raises(DRFValidationError) as exc:
        serializer.validate_document_file(spoofed)
    assert "Files of type" in str(exc.value) or "extension" in str(exc.value)
