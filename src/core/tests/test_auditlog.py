"""Tests for auditlog integration, proxy models, and encryption redaction."""

from __future__ import annotations

import pytest
from auditlog.models import LogEntry
from auditlog.registry import auditlog
from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from model_bakery import baker

from core.models import LogEntryProxy
from note.models import Note
from task.models import Task


@pytest.mark.django_db
def test_core_models_are_registered() -> None:
    assert auditlog.contains(apps.get_model("beach_wood_user", "BWUser"))
    assert auditlog.contains(apps.get_model("client", "Client"))
    assert auditlog.contains(apps.get_model("job", "Job"))
    assert auditlog.contains(apps.get_model("task", "Task"))
    assert auditlog.contains(apps.get_model("document", "Document"))
    assert auditlog.contains(apps.get_model("note", "Note"))
    assert auditlog.contains(apps.get_model("special_assignment", "SpecialAssignment"))

    assert auditlog.contains(apps.get_model("client", "ClientProxy"))
    assert auditlog.contains(apps.get_model("job", "JobProxy"))
    assert auditlog.contains(apps.get_model("task", "TaskProxy"))
    assert auditlog.contains(
        apps.get_model("special_assignment", "SpecialAssignmentProxy")
    )
    assert auditlog.contains(apps.get_model("assistant", "AssistantProxy"))
    assert auditlog.contains(apps.get_model("bookkeeper", "BookkeeperProxy"))
    assert auditlog.contains(apps.get_model("manager", "ManagerProxy"))


@pytest.mark.django_db
def test_log_entry_proxy_properties() -> None:
    user_cls = get_user_model()
    user = user_cls.objects.create_user(
        email="test_audit_user@example.com",
        password="test_password",
    )

    content_type_cls = apps.get_model("contenttypes", "ContentType")
    content_type = content_type_cls.objects.get_for_model(user)

    entry = LogEntry.objects.create(
        content_type=content_type,
        object_pk=str(user.pk),
        object_repr=str(user),
        action=LogEntry.Action.CREATE,
        actor=user,
        changes={"email": ["None", "test_audit_user@example.com"]},
    )
    proxy = LogEntryProxy.objects.get(pk=entry.pk)

    assert proxy.datetime == proxy.timestamp
    assert proxy.user == user
    assert proxy.get_event_type_display() == "Create"


@pytest.mark.django_db
def test_log_entry_proxy_soft_delete_and_update() -> None:
    user_cls = get_user_model()
    user = user_cls.objects.create_user(
        email="test_audit_user_2@example.com",
        password="test_password",
    )
    content_type_cls = apps.get_model("contenttypes", "ContentType")
    content_type = content_type_cls.objects.get_for_model(user)

    entry_delete = LogEntry.objects.create(
        content_type=content_type,
        object_pk=str(user.pk),
        object_repr=str(user),
        action=LogEntry.Action.UPDATE,
        changes={"is_deleted": [False, True]},
    )
    proxy_delete = LogEntryProxy.objects.get(pk=entry_delete.pk)
    assert proxy_delete.is_custom_deleted is True
    assert proxy_delete.is_custom_update is False

    entry_update = LogEntry.objects.create(
        content_type=content_type,
        object_pk=str(user.pk),
        object_repr=str(user),
        action=LogEntry.Action.UPDATE,
        changes={"email": ["old@example.com", "new@example.com"]},
    )
    proxy_update = LogEntryProxy.objects.get(pk=entry_update.pk)
    assert proxy_update.is_custom_deleted is False
    assert proxy_update.is_custom_update is True


@pytest.mark.django_db
def test_backfill_command_execution() -> None:
    call_command("backfill_audit_logs")


@pytest.mark.django_db
def test_auditlog_redacts_encrypted_fields_on_create_and_update() -> None:
    note = baker.make(
        Note,
        title="Public Note Title",
        body="Highly confidential note plaintext 123",
    )
    create_entry = LogEntry.objects.filter(
        object_pk=str(note.pk), action=LogEntry.Action.CREATE
    ).first()
    assert create_entry is not None
    assert create_entry.changes["title"] == ["None", "Public Note Title"]
    assert create_entry.changes["body"] == ["None", "[ENCRYPTED]"]

    note.body = "Updated confidential note plaintext 456"
    note.save()

    update_entry = LogEntry.objects.filter(
        object_pk=str(note.pk), action=LogEntry.Action.UPDATE
    ).first()
    assert update_entry is not None
    assert update_entry.changes["body"] == ["[ENCRYPTED]", "[ENCRYPTED]"]


@pytest.mark.django_db
def test_auditlog_redacts_task_sensitive_fields() -> None:
    task = baker.make(
        Task,
        title="Audited Task Title",
        hints="Super secret hints",
        additional_notes="Classified additional notes",
    )
    create_entry = LogEntry.objects.filter(
        object_pk=str(task.pk), action=LogEntry.Action.CREATE
    ).first()
    assert create_entry is not None
    assert create_entry.changes["title"] == ["None", "Audited Task Title"]
    assert create_entry.changes["hints"] == ["None", "[ENCRYPTED]"]
    assert create_entry.changes["additional_notes"] == ["None", "[ENCRYPTED]"]


@pytest.mark.django_db
def test_redact_audit_history_command() -> None:
    user = get_user_model().objects.create_user(
        email="audit_redact_user@example.com",
        password="TestPassword123!",
    )
    content_type = ContentType.objects.get_for_model(user)

    entry = LogEntry.objects.create(
        content_type=content_type,
        object_pk=str(user.pk),
        object_repr=str(user),
        action=LogEntry.Action.UPDATE,
        changes={"email": ["old@example.com", "new@example.com"]},
    )
    LogEntry.objects.filter(pk=entry.pk).update(
        changes={
            "account_password": ["old_secret_pwd", "new_secret_pwd"],
            "email": ["old@example.com", "new@example.com"],
        },
        serialized_data={"account_password": "leaked_in_json"},
    )
    entry.refresh_from_db()

    call_command("redact_audit_history", dry_run=True)
    entry.refresh_from_db()
    assert entry.changes["account_password"] == [
        "old_secret_pwd",
        "new_secret_pwd",
    ]
    assert entry.serialized_data["account_password"] == "leaked_in_json"

    call_command("redact_audit_history")
    entry.refresh_from_db()
    assert entry.changes["account_password"] == ["[ENCRYPTED]", "[ENCRYPTED]"]
    assert entry.changes["email"] == ["old@example.com", "new@example.com"]
    assert entry.serialized_data["account_password"] == "[ENCRYPTED]"
