"""Auditlog signal handlers and redaction for sensitive fields."""

from __future__ import annotations

import json
from typing import Any

from auditlog.models import LogEntry
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

from core.fields.encrypted_fields import EncryptedFieldMixin
from core.models.fields.encrypted_field import (
    EncryptedCharField as LegacyEncryptedCharField,
)


REDACTED_LABEL = "[ENCRYPTED]"
SENSITIVE_FIELD_NAMES: frozenset[str] = frozenset({
    "body",
    "additional_notes",
    "hints",
    "account_password",
    "password",
})


def redact_field_value(val: Any) -> Any:
    """Return redacted label if value is present, otherwise preserve."""
    if val is None or val == "" or val == "None" or val == "null":
        return val
    if val in (REDACTED_LABEL, "[REDACTED_CONFIDENTIAL]"):
        return val
    return REDACTED_LABEL


def get_sensitive_fields_for_model(
    model_cls: type[models.Model] | None,
) -> set[str]:
    """Resolve sensitive field names for a model class."""
    sensitive = set(SENSITIVE_FIELD_NAMES)
    if model_cls is not None:
        for field in model_cls._meta.get_fields():
            if isinstance(
                field, (EncryptedFieldMixin, LegacyEncryptedCharField)
            ) or getattr(field, "is_encrypted", False):
                sensitive.add(field.name)
                if hasattr(field, "attname"):
                    sensitive.add(field.attname)
    return sensitive


def redact_changes_dict(
    changes: dict[str, Any], sensitive_fields: set[str] | frozenset[str]
) -> tuple[dict[str, Any], bool]:
    """Scrub sensitive field values inside auditlog changes dictionary."""
    modified = False
    for field in sensitive_fields:
        if field in changes:
            diff = changes[field]
            if isinstance(diff, (list, tuple)) and len(diff) == 2:
                old_val, new_val = diff
                redacted_old = redact_field_value(old_val)
                redacted_new = redact_field_value(new_val)
                if [redacted_old, redacted_new] != list(diff):
                    changes[field] = [redacted_old, redacted_new]
                    modified = True
            else:
                redacted = redact_field_value(diff)
                if redacted != diff:
                    changes[field] = redacted
                    modified = True
    return changes, modified


def redact_serialized_dict(
    serialized_data: dict[str, Any], sensitive_fields: set[str] | frozenset[str]
) -> tuple[dict[str, Any], bool]:
    """Scrub sensitive field values inside auditlog serialized_data."""
    modified = False
    for field in sensitive_fields:
        if field in serialized_data:
            val = serialized_data[field]
            redacted = redact_field_value(val)
            if redacted != val:
                serialized_data[field] = redacted
                modified = True
    return serialized_data, modified


def sanitize_log_entry(instance: LogEntry) -> bool:
    """Scrub changes and serialized_data on a LogEntry instance."""
    model_cls: type[models.Model] | None = None
    if instance.content_type_id:
        try:
            model_cls = instance.content_type.model_class()
        except LookupError, AttributeError:
            model_cls = None

    sensitive_fields = get_sensitive_fields_for_model(model_cls)
    modified = False

    if instance.changes:
        if isinstance(instance.changes, str):
            try:
                changes_dict = json.loads(instance.changes)
                changes_dict, was_modified = redact_changes_dict(
                    changes_dict, sensitive_fields
                )
                if was_modified:
                    instance.changes = json.dumps(changes_dict)
                    modified = True
            except json.JSONDecodeError, ValueError, TypeError:
                pass
        elif isinstance(instance.changes, dict):
            changes_dict = dict(instance.changes)
            changes_dict, was_modified = redact_changes_dict(
                changes_dict, sensitive_fields
            )
            if was_modified:
                instance.changes = changes_dict
                modified = True

    if instance.serialized_data:
        if isinstance(instance.serialized_data, str):
            try:
                data_dict = json.loads(instance.serialized_data)
                data_dict, was_modified = redact_serialized_dict(
                    data_dict, sensitive_fields
                )
                if was_modified:
                    instance.serialized_data = json.dumps(data_dict)
                    modified = True
            except json.JSONDecodeError, ValueError, TypeError:
                pass
        elif isinstance(instance.serialized_data, dict):
            data_dict = dict(instance.serialized_data)
            data_dict, was_modified = redact_serialized_dict(
                data_dict, sensitive_fields
            )
            if was_modified:
                instance.serialized_data = data_dict
                modified = True

    return modified


@receiver(pre_save, sender=LogEntry)
@receiver(pre_save, sender="core.LogEntryProxy")
def redact_log_entry_pre_save(
    sender: type[models.Model], instance: LogEntry, **kwargs: Any
) -> None:
    """Intercept LogEntry pre-save to scrub encrypted and sensitive values."""
    sanitize_log_entry(instance)
