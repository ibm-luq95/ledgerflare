"""Tests for upload size settings and MIME/extension constants."""

from __future__ import annotations

import pytest
from django.conf import settings

from core.constants.file_types_validation import (
    DOCUMENTS_FT,
    EXTENSION_TO_MIME_MAP,
    IMAGES_AND_DOCS_FT,
    IMAGES_FT,
)


@pytest.mark.unit
def test_upload_settings_configured() -> None:
    """Verify max upload size settings exist and match default quotas."""
    assert settings.MAX_DOCUMENT_UPLOAD_SIZE == 100 * 1024 * 1024
    assert settings.MAX_IMAGE_UPLOAD_SIZE == 15 * 1024 * 1024


@pytest.mark.unit
def test_mime_constants_and_extension_map() -> None:
    """Verify webp in IMAGES_FT and EXTENSION_TO_MIME_MAP contains valid pairs."""
    assert "image/webp" in IMAGES_FT
    assert ".pdf" in EXTENSION_TO_MIME_MAP
    assert "application/pdf" in EXTENSION_TO_MIME_MAP[".pdf"]
    assert ".png" in EXTENSION_TO_MIME_MAP
    assert "image/png" in EXTENSION_TO_MIME_MAP[".png"]
    assert ".jpg" in EXTENSION_TO_MIME_MAP
    assert "image/jpeg" in EXTENSION_TO_MIME_MAP[".jpg"]
    assert ".webp" in EXTENSION_TO_MIME_MAP
    assert "image/webp" in EXTENSION_TO_MIME_MAP[".webp"]
    assert ".csv" in EXTENSION_TO_MIME_MAP
    assert "text/csv" in EXTENSION_TO_MIME_MAP[".csv"]
