"""Unit tests for migrate_db_encryption safeguards, concurrency conflicts, and --reverse rollback."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from django.core.management import call_command

from client_account.models import ClientAccountProxy


@pytest.mark.django_db
def test_migrate_db_reverse_reverts_ciphertext_to_plaintext(
    tmp_path: Path,
) -> None:
    """Verify that --reverse decrypts v1: ciphertexts and clears trigrams."""
    # 1. Create plaintext account and migrate it to encrypted
    acc = ClientAccountProxy.objects.create(
        account_name="Wells Fargo Reversal",
        account_url="https://wellsfargo.com/reversal",
        account_username="reversal_user",
        account_password="PlainReversalPassword123!",
    )

    # Forward migration to encrypted
    call_command("migrate_db_encryption", execute=True)

    # Verify fields are encrypted in DB
    raw_acc = (
        ClientAccountProxy.objects
        .filter(pk=acc.pk)
        .values(
            "account_password",
            "account_url",
            "account_username",
            "account_url_bidx",
            "account_username_bidx",
        )
        .first()
    )
    assert raw_acc is not None
    assert raw_acc["account_password"].startswith("v1:")
    assert raw_acc["account_url"].startswith("v1:")
    assert len(raw_acc["account_url_bidx"]) > 0

    # 2. Reverse rollback to plaintext
    call_command("migrate_db_encryption", reverse=True, execute=True)

    # Verify database fields are clean plaintext and trigrams are cleared
    reverted_acc = (
        ClientAccountProxy.objects
        .filter(pk=acc.pk)
        .values(
            "account_password",
            "account_url",
            "account_username",
            "account_url_bidx",
            "account_username_bidx",
        )
        .first()
    )
    assert reverted_acc is not None
    assert not reverted_acc["account_password"].startswith("v1:")
    assert reverted_acc["account_password"] == "PlainReversalPassword123!"
    assert not reverted_acc["account_url"].startswith("v1:")
    assert reverted_acc["account_url"] == "https://wellsfargo.com/reversal"
    assert reverted_acc["account_url_bidx"] == []
    assert reverted_acc["account_username_bidx"] == []

    # 3. Idempotent: running reverse again skips
    call_command("migrate_db_encryption", reverse=True, execute=True)
    post_reverted = (
        ClientAccountProxy.objects.filter(pk=acc.pk).values("account_password").first()
    )
    assert post_reverted["account_password"] == "PlainReversalPassword123!"


@pytest.mark.django_db
def test_migrate_db_reports_generated(tmp_path: Path) -> None:
    """Verify that migrate_db_encryption produces JSON and Markdown reports."""
    acc = ClientAccountProxy.objects.create(
        account_name="Report Account",
        account_url="https://report.com",
        account_username="reporter",
        account_password="password",
    )
    # Simulate unmigrated raw plaintext record in DB
    ClientAccountProxy.objects.filter(pk=acc.pk).update(
        account_password="plain_password",
        account_url="https://plain-url.com",
    )

    call_command("migrate_db_encryption", execute=True)

    report_dir = Path("logs/migration_reports")
    latest_json = report_dir / "migrate_db_encryption_latest.json"
    assert latest_json.exists()

    data = json.loads(latest_json.read_text(encoding="utf-8"))
    assert data["command"] == "migrate_db_encryption"
    assert data["mode"] == "execute"
    assert data["summary"]["total_migrated"] >= 1
