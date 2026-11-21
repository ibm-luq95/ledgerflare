from __future__ import annotations

import io
import json

import pytest
from django.apps import apps
from django.core.management import call_command
from model_bakery import baker

from core.crypto.engine import CryptoEngine
from task.models import TaskProxy


@pytest.mark.django_db
def test_migrate_encryption_dry_run_zero_mutations() -> None:
    out = io.StringIO()
    call_command("migrate_encryption", "--dry-run", stdout=out)
    output = out.getvalue()
    assert "DRY RUN COMPLETE" in output
    assert "Database mutations: 0" in output


@pytest.mark.django_db
def test_redact_audit_history_executes() -> None:
    out = io.StringIO()
    call_command("redact_audit_history", "--dry-run", stdout=out)
    output = out.getvalue()
    assert "AUDIT REDACTION DRY RUN COMPLETE" in output


@pytest.mark.django_db
def test_cleanup_plaintext_requires_confirm() -> None:
    out = io.StringIO()
    call_command("cleanup_plaintext_migration", stdout=out)
    output = out.getvalue()
    assert "Pass --confirm to execute cleanup" in output


@pytest.mark.django_db
def test_cleanup_plaintext_with_confirm() -> None:
    out = io.StringIO()
    call_command("cleanup_plaintext_migration", "--confirm", stdout=out)
    output = out.getvalue()
    assert "CLEANUP COMPLETE" in output


@pytest.mark.django_db
def test_migrate_encryption_execute_migrates_legacy_data() -> None:
    task = baker.make(TaskProxy, title="Legacy Task Migration")
    # Simulate legacy Fernet token in database
    legacy_fernet = CryptoEngine.encrypt("Confidential legacy note payload")
    TaskProxy.original_objects.filter(pk=task.pk).update(
        additional_notes=legacy_fernet, hints="Plaintext hint"
    )

    out = io.StringIO()
    call_command(
        "migrate_encryption",
        "--execute",
        "--model",
        "task.Task",
        stdout=out,
    )
    output = out.getvalue()
    assert "MIGRATION COMPLETE" in output

    # Check raw database value was upgraded to v1 envelope
    raw_row = (
        TaskProxy.original_objects
        .filter(pk=task.pk)
        .values("additional_notes", "hints")
        .first()
    )
    assert raw_row is not None
    assert raw_row["additional_notes"].startswith("v1:")
    assert raw_row["hints"].startswith("v1:")

    # Check transparent decryption via model descriptor
    reloaded = TaskProxy.objects.get(pk=task.pk)
    assert reloaded.additional_notes == "Confidential legacy note payload"
    assert reloaded.hints == "Plaintext hint"


@pytest.mark.django_db
def test_migrate_encryption_client_account_and_staff_accounts() -> None:
    from client_account.models import ClientAccountProxy
    from staff_briefcase.models.accounts.staff_accounts import StaffAccounts

    client_acc = baker.make(ClientAccountProxy, account_name="Legacy Client Acc")
    legacy_client_pwd = CryptoEngine.encrypt("LegacyClientSecret123!")
    ClientAccountProxy.original_objects.filter(pk=client_acc.pk).update(
        account_password=legacy_client_pwd
    )

    staff_acc = baker.make(StaffAccounts, title="Legacy Staff Acc")
    legacy_staff_pwd = CryptoEngine.encrypt("LegacyStaffSecret456!")
    StaffAccounts.original_objects.filter(pk=staff_acc.pk).update(
        password=legacy_staff_pwd
    )

    out = io.StringIO()
    call_command(
        "migrate_encryption",
        "--execute",
        stdout=out,
    )
    output = out.getvalue()
    assert "MIGRATION COMPLETE" in output

    raw_client = (
        ClientAccountProxy.original_objects
        .filter(pk=client_acc.pk)
        .values("account_password")
        .first()
    )
    assert raw_client is not None
    assert raw_client["account_password"].startswith("v1:")

    raw_staff = (
        StaffAccounts.original_objects
        .filter(pk=staff_acc.pk)
        .values("password")
        .first()
    )
    assert raw_staff is not None
    assert raw_staff["password"].startswith("v1:")

    reloaded_client = ClientAccountProxy.objects.get(pk=client_acc.pk)
    assert reloaded_client.account_password == "LegacyClientSecret123!"

    reloaded_staff = StaffAccounts.objects.get(pk=staff_acc.pk)
    assert reloaded_staff.password == "LegacyStaffSecret456!"


@pytest.mark.django_db
def test_redact_audit_history_actual_redaction() -> None:
    from django.contrib.contenttypes.models import ContentType

    try:
        log_entry_cls = apps.get_model("auditlog", "LogEntry")
    except LookupError:
        pytest.skip("Auditlog app not installed")

    task = baker.make(TaskProxy, title="Audit Redaction Target")
    ct = ContentType.objects.get_for_model(TaskProxy)
    changes = {
        "additional_notes": ["Old plaintext note", "New plaintext note"],
        "title": ["Old Title", "New Title"],
    }
    entry = log_entry_cls.objects.create(
        content_type=ct,
        object_pk=str(task.pk),
        object_repr=str(task),
        action=0,
        changes=json.dumps(changes),
    )

    out = io.StringIO()
    call_command("redact_audit_history", stdout=out)
    output = out.getvalue()
    assert "AUDIT REDACTION COMPLETE" in output

    entry.refresh_from_db()
    updated_changes = json.loads(entry.changes)
    assert updated_changes["additional_notes"] == [
        "[ENCRYPTED]",
        "[ENCRYPTED]",
    ]
    # Non-sensitive fields remain unmodified
    assert updated_changes["title"] == ["Old Title", "New Title"]
