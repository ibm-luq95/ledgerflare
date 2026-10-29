"""Tests for rotate_encryption_key management command."""

from __future__ import annotations

import os
from io import StringIO

import pytest
from django.core.management import call_command
from model_bakery import baker

from client_account.models import ClientAccountProxy
from note.models import NoteProxy


@pytest.fixture
def rotation_keys(settings: pytest.MonkeyPatch) -> tuple[str, str]:
    """Configure settings with k1 and k2 keys."""
    key_k1 = os.urandom(32).hex()
    key_k2 = os.urandom(32).hex()
    settings.CONTENT_ENCRYPTION_KEYS = {"k1": key_k1, "k2": key_k2}
    settings.ACTIVE_KEY_ID = "k1"
    settings.CONTENT_ENCRYPTION_KEY = key_k1
    return key_k1, key_k2


@pytest.mark.security
@pytest.mark.django_db
def test_rotate_encryption_key_live_execution(
    rotation_keys: tuple[str, str], settings: pytest.MonkeyPatch
) -> None:
    """Verify rotate_encryption_key command re-encrypts rows from k1 to k2."""
    account = baker.make(ClientAccountProxy, account_password="SuperSecretPassword1!")
    note = baker.make(NoteProxy, body="Confidential note content")

    raw_acc_before = ClientAccountProxy.objects.filter(pk=account.pk).values_list(
        "account_password", flat=True
    )[0]
    raw_note_before = NoteProxy.objects.filter(pk=note.pk).values_list(
        "body", flat=True
    )[0]
    assert raw_acc_before.startswith("v1:k1:")
    assert raw_note_before.startswith("v1:k1:")

    out = StringIO()
    call_command("rotate_encryption_key", from_key="k1", to_key="k2", stdout=out)

    account.refresh_from_db()
    note.refresh_from_db()

    raw_acc_after = ClientAccountProxy.objects.filter(pk=account.pk).values_list(
        "account_password", flat=True
    )[0]
    raw_note_after = NoteProxy.objects.filter(pk=note.pk).values_list(
        "body", flat=True
    )[0]
    assert raw_acc_after.startswith("v1:k2:")
    assert raw_note_after.startswith("v1:k2:")

    assert account.account_password == "SuperSecretPassword1!"
    assert note.body == "Confidential note content"


@pytest.mark.security
@pytest.mark.django_db
def test_rotate_soft_deleted_records(rotation_keys: tuple[str, str]) -> None:
    """Verify soft-deleted records are also rotated via original_objects manager."""
    note = baker.make(NoteProxy, body="Soft-deleted secret", is_deleted=True)
    raw_before = NoteProxy.original_objects.filter(pk=note.pk).values_list(
        "body", flat=True
    )[0]
    assert raw_before.startswith("v1:k1:")

    call_command("rotate_encryption_key", from_key="k1", to_key="k2")

    note.refresh_from_db()
    raw_after = NoteProxy.original_objects.filter(pk=note.pk).values_list(
        "body", flat=True
    )[0]
    assert raw_after.startswith("v1:k2:")
    assert note.body == "Soft-deleted secret"


@pytest.mark.security
@pytest.mark.django_db
def test_rotate_encryption_key_dry_run(rotation_keys: tuple[str, str]) -> None:
    """Verify --dry-run reports counts but does not modify database."""
    account = baker.make(ClientAccountProxy, account_password="DryRunPassword1!")
    raw_before = ClientAccountProxy.objects.filter(pk=account.pk).values_list(
        "account_password", flat=True
    )[0]
    assert raw_before.startswith("v1:k1:")

    out = StringIO()
    call_command(
        "rotate_encryption_key", from_key="k1", to_key="k2", dry_run=True, stdout=out
    )

    account.refresh_from_db()
    raw_after = ClientAccountProxy.objects.filter(pk=account.pk).values_list(
        "account_password", flat=True
    )[0]
    assert raw_after == raw_before
    assert "DRY RUN" in out.getvalue()


@pytest.mark.security
@pytest.mark.django_db
def test_corrupted_record_is_skipped_and_logged(rotation_keys: tuple[str, str]) -> None:
    """Verify a record with invalid ciphertext is skipped and does not crash the rotation."""
    account_good = baker.make(ClientAccountProxy, account_password="GoodPassword1!")
    account_bad = baker.make(ClientAccountProxy, account_password="BadPassword1!")

    # Corrupt account_bad ciphertext directly in DB
    corrupt_ct = "v1:k1:AAAA:corrupted_ciphertext:AAAA"
    ClientAccountProxy.objects.filter(pk=account_bad.pk).update(
        account_password=corrupt_ct
    )

    out = StringIO()
    err = StringIO()
    call_command(
        "rotate_encryption_key",
        from_key="k1",
        to_key="k2",
        stdout=out,
        stderr=err,
    )

    account_good.refresh_from_db()
    raw_good_after = ClientAccountProxy.objects.filter(pk=account_good.pk).values_list(
        "account_password", flat=True
    )[0]
    raw_bad_after = ClientAccountProxy.objects.filter(pk=account_bad.pk).values_list(
        "account_password", flat=True
    )[0]

    # Good account was rotated
    assert raw_good_after.startswith("v1:k2:")
    # Bad account was untouched and skipped
    assert raw_bad_after == corrupt_ct
    assert "Failed decrypting" in err.getvalue()


@pytest.mark.security
@pytest.mark.django_db
def test_rotate_filters_by_app_and_model(rotation_keys: tuple[str, str]) -> None:
    """Verify --app and --model flags restrict re-encryption scope."""
    account = baker.make(ClientAccountProxy, account_password="AppFilteredPass!")
    note = baker.make(NoteProxy, body="NoteShouldNotBeRotated")

    out = StringIO()
    call_command(
        "rotate_encryption_key",
        from_key="k1",
        to_key="k2",
        app="client_account",
        model="clientaccount",
        stdout=out,
    )

    raw_acc = ClientAccountProxy.objects.filter(pk=account.pk).values_list(
        "account_password", flat=True
    )[0]
    raw_note = NoteProxy.objects.filter(pk=note.pk).values_list("body", flat=True)[0]

    # Account was rotated because of filter match
    assert raw_acc.startswith("v1:k2:")
    # Note was skipped because model did not match
    assert raw_note.startswith("v1:k1:")


@pytest.mark.security
@pytest.mark.django_db
def test_rotate_legacy_fernet_records(rotation_keys: tuple[str, str]) -> None:
    """Verify legacy Fernet v2$ records are rotated directly into v1:k2: format."""
    from core.crypto.engine import CryptoEngine

    legacy_secret = "LegacyPasswordToRotate999!"
    legacy_ciphertext = CryptoEngine.encrypt(legacy_secret)
    assert legacy_ciphertext.startswith("v2$")

    account = baker.make(ClientAccountProxy)
    ClientAccountProxy.objects.filter(pk=account.pk).update(
        account_password=legacy_ciphertext
    )

    out = StringIO()
    call_command("rotate_encryption_key", from_key="legacy", to_key="k2", stdout=out)

    raw_acc_after = ClientAccountProxy.objects.filter(pk=account.pk).values_list(
        "account_password", flat=True
    )[0]
    assert raw_acc_after.startswith("v1:k2:")

    account.refresh_from_db()
    assert account.account_password == legacy_secret
