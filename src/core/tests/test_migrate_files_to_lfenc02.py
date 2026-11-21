"""Unit tests for migrate_files_to_lfenc02 management command."""

from __future__ import annotations

from pathlib import Path

import pytest
from django.core.files.base import ContentFile
from django.core.management import call_command

from core.crypto.container import MAGIC as MAGIC_V2
from document.models import DocumentProxy


@pytest.mark.django_db
def test_migrate_files_command_dry_run_does_not_mutate(tmp_path: Path) -> None:
    """Verify that --dry-run scans files and reports without encrypting on disk."""
    doc = DocumentProxy.objects.create(title="Unencrypted Test Doc")
    doc.document_file.save("test_plain.txt", ContentFile(b"Initial"))

    raw_path = Path(doc.document_file.path)
    plaintext_content = b"Plaintext document body for dry run"
    raw_path.write_bytes(plaintext_content)

    with raw_path.open("rb") as f:
        header = f.read(8)
    assert header != MAGIC_V2

    # Run command in dry-run mode
    call_command("migrate_files_to_lfenc02", dry_run=True)

    with raw_path.open("rb") as f:
        header_after = f.read(8)
    assert header_after != MAGIC_V2
    assert raw_path.read_bytes() == plaintext_content


@pytest.mark.django_db
def test_migrate_files_command_executes_and_verifies_sha256(tmp_path: Path) -> None:
    """Verify that --execute encrypts files into LFENC02 and leaves them decryptable."""
    content = b"Confidential Financial Audit File Content 12345"
    doc = DocumentProxy.objects.create(title="Secret Financial Doc")
    doc.document_file.save("financial_secret.txt", ContentFile(b"Initial"))

    raw_path = Path(doc.document_file.path)
    raw_path.write_bytes(content)

    # Execute migration
    call_command("migrate_files_to_lfenc02", execute=True)

    with raw_path.open("rb") as f:
        header = f.read(8)
    assert header == MAGIC_V2

    # Verify through storage that decrypted content matches 100%
    with doc.document_file.open("rb") as f:
        decrypted = f.read()
    assert decrypted == content


@pytest.mark.django_db
def test_migrate_files_skips_already_encrypted(tmp_path: Path) -> None:
    """Verify that files already in LFENC02 format are skipped idempotently."""
    doc = DocumentProxy.objects.create(title="Already Encrypted Doc")
    doc.document_file.save("already.txt", ContentFile(b"Some text"))

    raw_path = Path(doc.document_file.path)
    # File is already saved as LFENC02 via EncryptedFileField
    with raw_path.open("rb") as f:
        assert f.read(8) == MAGIC_V2

    mtime1 = raw_path.stat().st_mtime

    # Execution should skip
    call_command("migrate_files_to_lfenc02", execute=True)
    mtime2 = raw_path.stat().st_mtime
    assert mtime1 == mtime2
