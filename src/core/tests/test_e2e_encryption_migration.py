"""End-to-End simulation test for the complete production encryption migration pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest
from django.core.files.base import ContentFile
from django.core.management import call_command

from client.models import ClientProxy
from client_account.filters import ClientAccountFilter
from client_account.models import ClientAccountProxy
from core.crypto.container import MAGIC as MAGIC_V2
from core.crypto.service import EncryptionService
from discussion.models import Discussion
from document.models import DocumentProxy
from note.models import NoteProxy
from staff_briefcase.models.notes import StaffNotes
from task.models import TaskProxy


@pytest.mark.django_db
def test_full_production_encryption_migration_pipeline(tmp_path: Path) -> None:
    """Full lifecycle simulation of zero-downtime production encryption upgrade."""
    client = ClientProxy.objects.create(name="Acme Financial Corp")

    # 1. Create client account and simulate unencrypted legacy state
    acc = ClientAccountProxy.objects.create(
        client=client,
        account_name="Acme QBO Account",
        account_username="acme_admin_user",
        account_url="https://quickbooks.intuit.com/login",
    )
    ClientAccountProxy.objects.filter(pk=acc.pk).update(
        account_username="acme_admin_user",
        account_url="https://quickbooks.intuit.com/login",
        account_username_bidx=[],
        account_url_bidx=[],
    )

    # 2. Create staff note and simulate unencrypted text
    sn = StaffNotes.objects.create(
        title="Acme Confidential Tax Audit Strategy",
        note="Client requested deduction on commercial equipment $45,000.",
    )
    StaffNotes.objects.filter(pk=sn.pk).update(
        note="Client requested deduction on commercial equipment $45,000."
    )

    # 3. Create document and simulate unencrypted file on disk
    doc_content = b"%PDF-1.4 Confidential Tax Audit Report 2026\nRevenue: $1,250,000"
    doc = DocumentProxy.objects.create(title="Acme 2026 Tax Return")
    doc.document_file.save("tax_return.pdf", ContentFile(b"init"))
    raw_doc_path = Path(doc.document_file.path)
    raw_doc_path.write_bytes(doc_content)

    # Verify pre-migration: disk file is raw unencrypted plaintext
    with raw_doc_path.open("rb") as f:
        assert f.read(8) != MAGIC_V2

    # Verify pre-migration dual-read: storage reads plaintext seamlessly without errors
    with doc.document_file.open("rb") as f:
        assert f.read() == doc_content

    # 4. Phase 2: Execute File Containerization
    call_command("migrate_files_to_lfenc02", execute=True)

    # Verify file is now a valid LFENC02 container
    with raw_doc_path.open("rb") as f:
        assert f.read(8) == MAGIC_V2

    # Refresh instance and verify transparent decryption via storage
    doc.refresh_from_db()
    with doc.document_file.storage.open(doc.document_file.name, "rb") as f:
        assert f.read() == doc_content

    # 5. Phase 2: Execute Database Record Encryption
    call_command("migrate_db_encryption", execute=True)

    # Verify database fields are encrypted with v1: envelope and trigrams are populated
    acc_row = (
        ClientAccountProxy.objects
        .filter(pk=acc.pk)
        .values(
            "account_username",
            "account_url",
            "account_username_bidx",
            "account_url_bidx",
        )
        .first()
    )
    assert acc_row is not None
    assert acc_row["account_username"].startswith(EncryptionService.VERSION_PREFIX_V1)
    assert acc_row["account_url"].startswith(EncryptionService.VERSION_PREFIX_V1)
    assert len(acc_row["account_username_bidx"]) > 0
    assert len(acc_row["account_url_bidx"]) > 0

    # Verify transparent model attribute decryption
    acc.refresh_from_db()
    assert acc.account_username == "acme_admin_user"
    assert acc.account_url == "https://quickbooks.intuit.com/login"

    # Verify partial substring search works via trigram blind index
    filter_set = ClientAccountFilter(
        data={"account_url": "quickbooks"},
        queryset=ClientAccountProxy.objects.all(),
    )
    assert acc in list(filter_set.qs)

    # 6. Phase 3: Cryptographic Integrity Audit
    # Must pass cleanly with 0 violations
    call_command("audit_encryption_integrity", full=True)
