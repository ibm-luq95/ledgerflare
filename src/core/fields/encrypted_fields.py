"""Transparent Django model fields supporting AES-256-GCM encryption."""

from __future__ import annotations

from typing import Any

from django.db import models
from django.db.models.fields import Field

from core.crypto.service import DecryptionIntegrityError, EncryptionService


class EncryptedFieldDescriptor:
    """Descriptor enabling transparent decryption on attribute access."""

    def __init__(self, field: Field) -> None:
        """Initialize descriptor with parent model field."""
        self.field = field

    def __get__(self, instance: Any, owner: Any = None) -> Any:
        """Decrypt ciphertext transparently when accessed via model instance."""
        if instance is None:
            return self

        raw_val = instance.__dict__.get(self.field.attname)
        if raw_val is None or not isinstance(raw_val, str):
            return raw_val

        prefixes = (EncryptionService.VERSION_PREFIX_V1, "v2$", "gAAAAA")
        if raw_val.startswith(prefixes):
            concrete = getattr(instance._meta, "concrete_model", None)
            model_name = (concrete or instance)._meta.model_name
            field_name = self.field.attname
            record_id = str(instance.pk) if instance.pk is not None else ""
            aad = f"{model_name}:{field_name}:{record_id}".encode()

            try:
                decrypted = EncryptionService.decrypt(raw_val, aad)
            except Exception as err:
                msg = (
                    f"Integrity check failed decrypting {model_name}.{field_name} "
                    f"(ID: {record_id})"
                )
                raise DecryptionIntegrityError(msg) from err
            else:
                instance.__dict__[self.field.attname] = decrypted
                return decrypted

        return raw_val

    def __set__(self, instance: Any, value: Any) -> None:
        """Assign value directly to instance dictionary."""
        instance.__dict__[self.field.attname] = value


class EncryptedFieldMixin:
    """Mixin providing database serialization hooks for encrypted fields."""

    descriptor_class = EncryptedFieldDescriptor

    def __init__(
        self,
        *args: Any,
        blind_index: bool = False,
        blind_index_field: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize encrypted field with optional blind index configuration."""
        self.blind_index = blind_index
        self.blind_index_field = blind_index_field
        super().__init__(*args, **kwargs)

    def contribute_to_class(
        self, cls: type[models.Model], name: str, private_only: bool = False
    ) -> None:
        """Attach descriptor to model class."""
        super().contribute_to_class(cls, name, private_only=private_only)  # type: ignore[misc]
        setattr(cls, self.attname, self.descriptor_class(self))  # type: ignore[arg-type, attr-defined]

    def pre_save(self, model_instance: models.Model, add: bool) -> Any:
        """Encrypt value and compute blind index if configured."""
        from core.crypto.blind_index import compute_blind_index

        value = model_instance.__dict__.get(self.attname)  # type: ignore[attr-defined]
        str_val = str(value) if value is not None else ""

        if self.blind_index:
            bidx_field_name = self.blind_index_field or f"{self.attname}_bidx"
            if hasattr(model_instance, bidx_field_name):
                concrete = getattr(model_instance._meta, "concrete_model", None)
                model_name = (concrete or model_instance)._meta.model_name
                context = f"{model_name}:{self.attname}"
                bidx = compute_blind_index(str_val, context=context) if str_val else ""
                setattr(model_instance, bidx_field_name, bidx)

        if value is None:
            return value

        if not str_val:
            return str_val

        if str_val.startswith(EncryptionService.VERSION_PREFIX_V1):
            return str_val

        concrete = getattr(model_instance._meta, "concrete_model", None)
        model_name = (concrete or model_instance)._meta.model_name
        field_name = self.attname  # type: ignore[attr-defined]
        record_id = str(model_instance.pk) if model_instance.pk is not None else ""
        aad = f"{model_name}:{field_name}:{record_id}".encode()

        return EncryptionService.encrypt(str_val, aad)

    def from_db_value(self, value: Any, expression: Any, connection: Any) -> Any:
        """Pass raw database value without eagerly decrypting."""
        return value

    def to_python(self, value: Any) -> Any:
        """Return value without altering encrypted representation."""
        return value


class EncryptedTextField(EncryptedFieldMixin, models.TextField):  # type: ignore[misc]
    """TextField transparently encrypting data at rest using AES-256-GCM."""

    description = "Field storing authenticated AES-256-GCM encrypted text"

    def deconstruct(self) -> tuple[str, str, list[Any], dict[str, Any]]:
        """Deconstruct field for migration generation."""
        name, _path, args, kwargs = super().deconstruct()
        if self.blind_index:
            kwargs["blind_index"] = True
        if self.blind_index_field:
            kwargs["blind_index_field"] = self.blind_index_field
        return (
            name,
            "core.fields.encrypted_fields.EncryptedTextField",
            list(args),
            kwargs,
        )


class EncryptedCharField(EncryptedFieldMixin, models.CharField):  # type: ignore[misc]
    """CharField transparently encrypting data at rest using AES-256-GCM."""

    description = "Field storing authenticated AES-256-GCM encrypted string"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize CharField with default max_length of 512."""
        kwargs.setdefault("max_length", 512)
        super().__init__(*args, **kwargs)

    def deconstruct(self) -> tuple[str, str, list[Any], dict[str, Any]]:
        """Deconstruct field for migration generation."""
        name, _path, args, kwargs = super().deconstruct()
        if self.blind_index:
            kwargs["blind_index"] = True
        if self.blind_index_field:
            kwargs["blind_index_field"] = self.blind_index_field
        return (
            name,
            "core.fields.encrypted_fields.EncryptedCharField",
            list(args),
            kwargs,
        )
