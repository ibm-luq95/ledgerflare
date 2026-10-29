"""Document model form with upload hardening and malware verification."""

from __future__ import annotations

from typing import Any

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from core.constants.file_types_validation import IMAGES_AND_DOCS_FT
from core.constants.form import EXCLUDED_FIELDS
from core.forms import BaseModelFormMixin
from core.forms.mixins.remove_fields_mixin import RemoveFieldsMixin
from core.forms.mixins.set_bookkeeper_related_mixin import (
    InitBookkeeperRelatedFieldsMixin,
)
from core.forms.mixins.set_field_to_hidden import SetFieldsInputsHiddenMixin
from core.services.malware_scanner import (
    ClamAVScanner,
    MalwareDetectedError,
    ScannerUnavailableError,
)
from core.utils import FileValidator
from document.models import Document


class DocumentForm(
    BaseModelFormMixin,
    RemoveFieldsMixin,
    InitBookkeeperRelatedFieldsMixin,
    SetFieldsInputsHiddenMixin,
):
    """Form for Document uploads and metadata management."""

    def __init__(
        self,
        removed_fields: list[str] | None = None,
        hidden_inputs: dict[str, Any] | None = None,
        bookkeeper: Any = None,
        is_update: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize DocumentForm with custom fields and context."""
        super().__init__(*args, **kwargs)
        RemoveFieldsMixin.__init__(self, removed_fields=removed_fields)
        SetFieldsInputsHiddenMixin.__init__(self, hidden_inputs=hidden_inputs)
        InitBookkeeperRelatedFieldsMixin.__init__(self, bookkeeper=bookkeeper)
        if is_update is True:
            self.fields["document_file"].widget.attrs["readonly"] = True
            self.fields["document_file"].required = False
        if self.initial.get("client") is not None:
            self.fields["client"].initial = self.initial.get("client")

    def clean_document_file(self) -> Any:
        """Validate uploaded document file size, MIME type, and malware via ClamAV."""
        file = self.cleaned_data.get("document_file")
        if file and isinstance(file, UploadedFile):
            max_size = getattr(settings, "MAX_DOCUMENT_UPLOAD_SIZE", 100 * 1024 * 1024)
            validator = FileValidator(
                max_size=max_size,
                content_types=IMAGES_AND_DOCS_FT,
            )
            validator(file)

            scanner = ClamAVScanner()
            try:
                scanner.scan_stream(file)
            except MalwareDetectedError as err:
                msg = str(err)
                raise forms.ValidationError(msg) from err
            except ScannerUnavailableError as err:
                msg = "Malware scanner temporarily unavailable. Please try again later."
                raise forms.ValidationError(msg) from err
        return file

    class Meta(BaseModelFormMixin.Meta):
        """Meta options for DocumentForm."""

        model = Document
        exclude = EXCLUDED_FIELDS
