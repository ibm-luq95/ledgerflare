"""Unit tests for migrate_files_to_lfenc02 safeguards, quarantine, and --reverse rollback."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from django.core.files.base import ContentFile
from django.core.management import call_command

from core.crypto.container import MAGIC as MAGIC_V2
from document.models import DocumentProxy


@pytest.mark.django_db
def test_migrate_files_missing_file_quarantined(tmp_path: Path) -> None:
    """Verify that records with missing disk files are quarantined without halting."""
    doc = DocumentProxy.objects.create(title="Dangling Document")
    doc.document_file.save("missing_invoice.pdf", ContentFile(b"init"))
    raw_path = Path(doc.document_file.path)

    # Simulate missing file on disk
    if raw_path.exists():
        raw_path.unlink()
    assert not raw_path.exists()

    # Run migration in execute mode
    call_command("migrate_files_to_lfenc02", execute=True)

    # Check report directory
    report_dir = Path("logs/migration_reports")
    latest_json = report_dir / "migrate_files_to_lfenc02_latest.json"
    assert latest_json.exists()

    data = json.loads(latest_json.read_text(encoding="utf-8"))
    assert data["summary"]["total_quarantined"] >= 1
    quarantined_paths = [q["path"] for q in data["quarantined_items"]]
    assert str(raw_path) in quarantined_paths


@pytest.mark.django_db
def test_migrate_files_reverse_reverts_container_to_plaintext(
    tmp_path: Path,
) -> None:
    """Verify that --reverse decrypts an LFENC02 container back to plain file."""
    content = b"Confidential Reversal Test Payload 12345"
    doc = DocumentProxy.objects.create(title="Reversal Doc")
    doc.document_file.save("reversal.txt", ContentFile(b"init"))
    raw_path = Path(doc.document_file.path)
    raw_path.write_bytes(content)

    # 1. Forward migration to LFENC02
    call_command("migrate_files_to_lfenc02", execute=True)
    with raw_path.open("rb") as f:
        assert f.read(8) == MAGIC_V2

    # 2. Reversal rollback to plaintext
    call_command("migrate_files_to_lfenc02", reverse=True, execute=True)
    with raw_path.open("rb") as f:
        assert f.read(8) != MAGIC_V2
    assert raw_path.read_bytes() == content

    # 3. Running reverse again should be idempotent and skip
    call_command("migrate_files_to_lfenc02", reverse=True, execute=True)
    assert raw_path.read_bytes() == content
