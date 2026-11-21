"""Tests for file upload validation rules."""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError

from core.utils import FileValidator


@pytest.mark.unit
def test_file_validator_size_and_content_type() -> None:
    """Verify FileValidator enforces max size limits."""
    validator = FileValidator(
        max_size=1024 * 1000, content_types=("image/png", "image/jpeg")
    )

    class DummyFile:
        size = 2000000
        content_type = "image/png"
        name = "test.png"

    with pytest.raises(ValidationError):
        validator(DummyFile())
