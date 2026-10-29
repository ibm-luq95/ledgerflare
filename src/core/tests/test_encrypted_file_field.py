from __future__ import annotations

import pytest
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models

from core.fields.encrypted_file_field import EncryptedFileField, EncryptedImageField
from core.storage.encrypted_storage import EncryptedPrivateStorage
from core.utils.file_upload_validator import FileValidator
from document.models import Document


def test_encrypted_file_field_attaches_default_validator() -> None:
    field = EncryptedFileField(upload_to="uploads/")
    assert len(field.validators) > 0
    validator = field.validators[0]
    assert isinstance(validator, FileValidator)
    assert validator.max_size == settings.MAX_DOCUMENT_UPLOAD_SIZE


def test_encrypted_image_field_attaches_default_validator() -> None:
    field = EncryptedImageField(upload_to="images/")
    assert len(field.validators) > 0
    validator = field.validators[0]
    assert isinstance(validator, FileValidator)
    assert validator.max_size == settings.MAX_IMAGE_UPLOAD_SIZE


def test_encrypted_file_field_default_storage() -> None:
    field = EncryptedFileField(upload_to="test_uploads/")
    assert isinstance(field.storage, EncryptedPrivateStorage)


def test_encrypted_image_field_default_storage() -> None:
    field = EncryptedImageField(upload_to="test_images/")
    assert isinstance(field.storage, EncryptedPrivateStorage)


def test_encrypted_file_field_deconstruct() -> None:
    field = EncryptedFileField(upload_to="uploads/")
    _name, path, _args, kwargs = field.deconstruct()
    assert path == "core.fields.encrypted_file_field.EncryptedFileField"
    assert kwargs.get("upload_to") == "uploads/"
    assert "validators" not in kwargs


def test_encrypted_image_field_deconstruct() -> None:
    field = EncryptedImageField(upload_to="images/")
    _name, path, _args, kwargs = field.deconstruct()
    assert path == "core.fields.encrypted_file_field.EncryptedImageField"
    assert kwargs.get("upload_to") == "images/"
    assert "validators" not in kwargs


@pytest.mark.django_db
def test_document_model_uses_encrypted_file_field() -> None:
    field = Document._meta.get_field("document_file")
    assert isinstance(field, EncryptedFileField)
    assert isinstance(field.storage, EncryptedPrivateStorage)

    content = b"Financial invoice and contract agreement"
    doc = Document.objects.create(
        title="Agreement Doc",
        document_file=ContentFile(content, name="invoice.pdf"),
    )

    doc.refresh_from_db()
    with doc.document_file.open("rb") as f:
        assert f.read() == content
