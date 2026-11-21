"""Unit tests for migrate_db_encryption management command."""

from __future__ import annotations

import pytest
from django.core.management import call_command

from client_account.models import ClientAccountProxy
from core.crypto.service import EncryptionService


@pytest.mark.django_db
def test_migrate_db_encryption_dry_run_does_not_mutate() -> None:
    """Verify that --dry-run scans records without mutating DB fields."""
    acc = ClientAccountProxy.objects.create(
        account_name="Dry Run Account",
        account_username="plain_dry_user",
        account_url="https://example.com/dry",
    )
    # Simulate unmigrated state by directly writing plaintext via update
    ClientAccountProxy.objects.filter(pk=acc.pk).update(
        account_username="plain_dry_user",
        account_username_bidx=[],
    )

    call_command("migrate_db_encryption", dry_run=True)

    acc.refresh_from_db()
    raw_user = acc.__dict__["account_username"]
    assert not raw_user.startswith(EncryptionService.VERSION_PREFIX_V1)


@pytest.mark.django_db
def test_migrate_db_encryption_executes_and_populates_trigrams() -> None:
    """Verify that --execute encrypts records, binds AAD, and populates trigram blind indexes."""
    acc = ClientAccountProxy.objects.create(
        account_name="Live Exec Account",
        account_username="chase_operator",
        account_url="https://chase.com/admin",
    )
    # Simulate unmigrated state by directly writing plaintext
    ClientAccountProxy.objects.filter(pk=acc.pk).update(
        account_username="chase_operator",
        account_username_bidx=[],
    )

    call_command("migrate_db_encryption", execute=True)

    # Check raw DB value via values() bypassing descriptor cache
    db_row = (
        ClientAccountProxy.objects
        .filter(pk=acc.pk)
        .values("account_username", "account_username_bidx")
        .first()
    )
    assert db_row is not None
    assert db_row["account_username"].startswith(EncryptionService.VERSION_PREFIX_V1)
    assert len(db_row["account_username_bidx"]) > 0

    # Decryptable transparently via model instance
    acc.refresh_from_db()
    assert acc.account_username == "chase_operator"


@pytest.mark.django_db
def test_migrate_db_encryption_skips_already_encrypted() -> None:
    """Verify that already encrypted records (v1:) are skipped idempotently."""
    acc = ClientAccountProxy.objects.create(
        account_name="Already Encrypted",
        account_username="already_v1_user",
    )
    call_command("migrate_db_encryption", execute=True)
    acc.refresh_from_db()
    updated_at_1 = acc.updated_at

    # Second pass should not touch already migrated record
    call_command("migrate_db_encryption", execute=True)
    acc.refresh_from_db()
    updated_at_2 = acc.updated_at
    assert updated_at_1 == updated_at_2
