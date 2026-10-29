"""Upload file validator with bounded-memory MIME sniffing."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

import magic
from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat
from django.utils.deconstruct import deconstructible

from core.constants.file_types_validation import EXTENSION_TO_MIME_MAP


@deconstructible
class FileValidator:
    """Validates uploaded files based on size, sniffed MIME type, and extension."""

    SNIFF_BUFFER_SIZE = 4096

    error_messages: ClassVar[dict[str, str]] = {
        "max_size": (
            "Ensure this file size is not greater than %(max_size)s. "
            "Your file size is %(size)s."
        ),
        "min_size": (
            "Ensure this file size is not less than %(min_size)s. "
            "Your file size is %(size)s."
        ),
        "content_type": "Files of type %(content_type)s are not supported.",
        "extension_mismatch": (
            "File extension '%(extension)s' does not match detected file "
            "type '%(content_type)s'."
        ),
        "disallowed_extension": "File extension '%(extension)s' is not supported.",
    }

    def __init__(
        self,
        max_size: int | None = None,
        min_size: int | None = None,
        content_types: tuple[str, ...] | list[str] = (),
        allowed_extensions: tuple[str, ...] | list[str] | None = None,
    ) -> None:
        """Initialize FileValidator with size thresholds and allowed types."""
        self.max_size = max_size
        self.min_size = min_size
        self.content_types = tuple(content_types)
        self.allowed_extensions = (
            tuple(allowed_extensions) if allowed_extensions is not None else None
        )

    def __call__(self, data: Any) -> None:
        """Validate uploaded file size, sniff MIME bytes, and verify extension."""
        file_size = getattr(data, "size", None)
        if file_size is not None and isinstance(file_size, (int, float)):
            if self.max_size is not None and file_size > self.max_size:
                params = {
                    "max_size": filesizeformat(self.max_size),
                    "size": filesizeformat(file_size),
                }
                raise ValidationError(
                    self.error_messages["max_size"], "max_size", params
                )

            if self.min_size is not None and file_size < self.min_size:
                params = {
                    "min_size": filesizeformat(self.min_size),
                    "size": filesizeformat(file_size),
                }
                raise ValidationError(
                    self.error_messages["min_size"], "min_size", params
                )

        if self.content_types:
            if hasattr(data, "seek"):
                data.seek(0)
            header = data.read(self.SNIFF_BUFFER_SIZE)
            if hasattr(data, "seek"):
                data.seek(0)

            content_type = magic.from_buffer(header, mime=True)

            if content_type not in self.content_types:
                params = {"content_type": content_type}
                raise ValidationError(
                    self.error_messages["content_type"], "content_type", params
                )

            filename = getattr(data, "name", None)
            if filename:
                ext = Path(filename).suffix.lower()
                if ext:
                    if (
                        self.allowed_extensions is not None
                        and ext not in self.allowed_extensions
                    ):
                        params = {"extension": ext}
                        raise ValidationError(
                            self.error_messages["disallowed_extension"],
                            "disallowed_extension",
                            params,
                        )

                    allowed_mimes = EXTENSION_TO_MIME_MAP.get(ext)
                    if allowed_mimes is None:
                        params = {"extension": ext}
                        raise ValidationError(
                            self.error_messages["disallowed_extension"],
                            "disallowed_extension",
                            params,
                        )

                    if content_type not in allowed_mimes:
                        params = {"extension": ext, "content_type": content_type}
                        raise ValidationError(
                            self.error_messages["extension_mismatch"],
                            "extension_mismatch",
                            params,
                        )

    def __eq__(self, other: Any) -> bool:
        """Check equality between FileValidator instances."""
        return (
            isinstance(other, FileValidator)
            and self.max_size == other.max_size
            and self.min_size == other.min_size
            and self.content_types == other.content_types
            and self.allowed_extensions == other.allowed_extensions
        )

    def __hash__(self) -> int:
        """Hash FileValidator based on its configuration."""
        return hash(
            (
                self.max_size,
                self.min_size,
                self.content_types,
                self.allowed_extensions,
            )
        )
