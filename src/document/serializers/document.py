"""Document model serializer with malware scanning and upload validation."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.uploadedfile import UploadedFile
from rest_framework import serializers

from client.models import ClientProxy
from core.constants import EXCLUDED_FIELDS
from core.constants.file_types_validation import IMAGES_AND_DOCS_FT
from core.services.malware_scanner import (
    ClamAVScanner,
    MalwareDetectedError,
    ScannerUnavailableError,
)
from core.utils import FileValidator
from document.models import Document
from job.models import JobProxy


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model instances with upload verification."""

    job = serializers.PrimaryKeyRelatedField(
        queryset=JobProxy.objects.all(),
        many=False,
        required=False,
    )
    client = serializers.PrimaryKeyRelatedField(
        queryset=ClientProxy.objects.all(), many=False, required=False
    )

    def validate_document_file(self, value: Any) -> Any:
        """Validate uploaded document file size, MIME type, and malware via ClamAV."""
        if value and isinstance(value, UploadedFile):
            max_size = getattr(settings, "MAX_DOCUMENT_UPLOAD_SIZE", 100 * 1024 * 1024)
            validator = FileValidator(
                max_size=max_size,
                content_types=IMAGES_AND_DOCS_FT,
            )
            try:
                validator(value)
            except DjangoValidationError as err:
                raise serializers.ValidationError(err.messages) from err

            scanner = ClamAVScanner()
            try:
                scanner.scan_stream(value)
            except MalwareDetectedError as err:
                msg = str(err)
                raise serializers.ValidationError(msg) from err
            except ScannerUnavailableError as err:
                msg = "Malware scanner temporarily unavailable. Please try again later."
                raise serializers.ValidationError(msg) from err
        return value

    class Meta:
        """Meta options for DocumentSerializer."""

        model = Document
        exclude = EXCLUDED_FIELDS
