"""Tests for staff briefcase document uploads with malware validation."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from core.services.malware_scanner import MalwareDetectedError
from staff_briefcase.forms import BriefcaseDocumentMiniForm
from staff_briefcase.serializers import StaffDocumentsSerializer


@pytest.mark.unit
def test_staff_documents_serializer_blocks_infected_file() -> None:
    """Verify StaffDocumentsSerializer blocks infected files and returns validation error."""
    eicar = SimpleUploadedFile(
        "threat.pdf",
        b"%PDF-1.4\nEICAR test payload",
        content_type="application/pdf",
    )
    serializer = StaffDocumentsSerializer(
        data={
            "title": "Threat Document",
            "briefcase": str(uuid.uuid4()),
            "document_file": eicar,
        }
    )
    with patch(
        "core.services.malware_scanner.ClamAVScanner.scan_stream",
        side_effect=MalwareDetectedError("Malware detected by scanner: Win.Test.EICAR"),
    ):
        assert not serializer.is_valid()
        assert "document_file" in serializer.errors
        assert any("Malware detected" in str(msg) for msg in serializer.errors["document_file"])


@pytest.mark.unit
def test_briefcase_document_mini_form_blocks_infected_file() -> None:
    """Verify BriefcaseDocumentMiniForm blocks infected files."""
    eicar = SimpleUploadedFile(
        "threat.pdf",
        b"%PDF-1.4\nEICAR test payload",
        content_type="application/pdf",
    )
    form = BriefcaseDocumentMiniForm(
        data={"title": "Threat Document", "briefcase": str(uuid.uuid4())},
        files={"document_file": eicar},
    )
    with patch(
        "core.services.malware_scanner.ClamAVScanner.scan_stream",
        side_effect=MalwareDetectedError("Malware detected by scanner: Win.Test.EICAR"),
    ):
        assert not form.is_valid()
        assert "document_file" in form.errors
        assert any("Malware detected" in str(msg) for msg in form.errors["document_file"])


@pytest.mark.unit
def test_briefcase_document_mini_form_accepts_clean_file() -> None:
    """Verify BriefcaseDocumentMiniForm accepts clean documents."""
    clean = SimpleUploadedFile(
        "clean.pdf",
        b"%PDF-1.4\nClean test document",
        content_type="application/pdf",
    )
    form = BriefcaseDocumentMiniForm(
        data={"title": "Clean Document", "briefcase": str(uuid.uuid4())},
        files={"document_file": clean},
    )
    with patch("core.services.malware_scanner.ClamAVScanner.scan_stream"):
        assert form.is_valid()
