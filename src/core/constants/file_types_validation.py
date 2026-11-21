"""File MIME types and extension mappings used for upload validation."""

from __future__ import annotations


IMAGES_FT: tuple[str, ...] = (
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
)

DOCUMENTS_FT: tuple[str, ...] = (
    "text/csv",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.oasis.opendocument.spreadsheet",
    "application/pdf",
    "text/plain",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.oasis.opendocument.text",
)

IMAGES_AND_DOCS_FT: tuple[str, ...] = IMAGES_FT + DOCUMENTS_FT

EXTENSION_TO_MIME_MAP: dict[str, tuple[str, ...]] = {
    ".pdf": ("application/pdf",),
    ".png": ("image/png",),
    ".jpg": ("image/jpeg",),
    ".jpeg": ("image/jpeg",),
    ".webp": ("image/webp",),
    ".csv": ("text/csv", "text/plain"),
    ".txt": ("text/plain",),
    ".doc": ("application/msword",),
    ".docx": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
    ),
    ".xls": ("application/vnd.ms-excel",),
    ".xlsx": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/zip",
    ),
    ".odt": ("application/vnd.oasis.opendocument.text",),
    ".ods": ("application/vnd.oasis.opendocument.spreadsheet",),
}
