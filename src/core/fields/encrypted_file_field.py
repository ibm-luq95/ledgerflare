"""Encrypted file and image model fields with upload limits."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.db import models

from core.constants.file_types_validation import IMAGES_AND_DOCS_FT, IMAGES_FT
from core.storage.encrypted_storage import EncryptedPrivateStorage
from core.utils.file_upload_validator import FileValidator


class EncryptedFileField(models.FileField):
    """FileField defaulting to EncryptedPrivateStorage and upload limits."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize EncryptedFileField with default storage and validator."""
        if kwargs.get("storage") is None:
            kwargs["storage"] = EncryptedPrivateStorage()
        if "validators" not in kwargs:
            max_size = getattr(settings, "MAX_DOCUMENT_UPLOAD_SIZE", 100 * 1024 * 1024)
            kwargs["validators"] = [
                FileValidator(max_size=max_size, content_types=IMAGES_AND_DOCS_FT)
            ]
            self._has_default_validator = True
        else:
            self._has_default_validator = False
        super().__init__(*args, **kwargs)

    def deconstruct(self) -> tuple[str, str, list[Any], dict[str, Any]]:
        """Deconstruct field for Django migration serialization."""
        name, _path, args, kwargs = super().deconstruct()
        if isinstance(self.storage, EncryptedPrivateStorage):
            kwargs.pop("storage", None)
        if getattr(self, "_has_default_validator", False):
            kwargs.pop("validators", None)
        return (
            name,
            "core.fields.encrypted_file_field.EncryptedFileField",
            list(args),
            kwargs,
        )


class EncryptedImageField(models.ImageField):
    """ImageField defaulting to EncryptedPrivateStorage and image limits."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize EncryptedImageField with default storage and validator."""
        if kwargs.get("storage") is None:
            kwargs["storage"] = EncryptedPrivateStorage()
        if "validators" not in kwargs:
            max_size = getattr(settings, "MAX_IMAGE_UPLOAD_SIZE", 15 * 1024 * 1024)
            kwargs["validators"] = [
                FileValidator(max_size=max_size, content_types=IMAGES_FT)
            ]
            self._has_default_validator = True
        else:
            self._has_default_validator = False
        super().__init__(*args, **kwargs)

    def deconstruct(self) -> tuple[str, str, list[Any], dict[str, Any]]:
        """Deconstruct field for Django migration serialization."""
        name, _path, args, kwargs = super().deconstruct()
        if isinstance(self.storage, EncryptedPrivateStorage):
            kwargs.pop("storage", None)
        if getattr(self, "_has_default_validator", False):
            kwargs.pop("validators", None)
        return (
            name,
            "core.fields.encrypted_file_field.EncryptedImageField",
            list(args),
            kwargs,
        )
