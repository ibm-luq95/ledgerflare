"""Unit tests for MigrationReporter."""

from __future__ import annotations

import json
from pathlib import Path

from core.crypto.reporter import MigrationReporter


def test_migration_reporter_metrics_aggregation(tmp_path: Path) -> None:
    """Verify metrics aggregation and counts calculation."""
    reporter = MigrationReporter(
        command_name="migrate_files_to_lfenc02",
        mode="execute",
    )

    reporter.record_target(
        target_name="document.Document (document_file)",
        total_count=100,
        migrated=95,
        skipped=3,
        quarantined=2,
        conflicts=0,
        errors=0,
    )
    reporter.record_target(
        target_name="staff_briefcase.StaffDocuments (document_file)",
        total_count=50,
        migrated=50,
        skipped=0,
        quarantined=0,
        conflicts=0,
        errors=0,
    )

    assert reporter.total_scanned == 150
    assert reporter.total_migrated == 145
    assert reporter.total_skipped == 3
    assert reporter.total_quarantined == 2
    assert reporter.total_conflicts == 0
    assert reporter.total_errors == 0


def test_migration_reporter_quarantine_tracking(tmp_path: Path) -> None:
    """Verify quarantine items tracking and structured output."""
    reporter = MigrationReporter(
        command_name="migrate_files_to_lfenc02",
        mode="execute",
    )

    reporter.record_quarantine(
        model="document.Document",
        pk="3fa85f64-5717-4562-b3fc-2c963f66afa6",
        field="document_file",
        path="documents/2024/missing_invoice.pdf",
        issue_type="MISSING_FILE",
        error="FileNotFoundError: [Errno 2] No such file or directory",
    )

    assert len(reporter.quarantined_items) == 1
    item = reporter.quarantined_items[0]
    assert item["model"] == "document.Document"
    assert item["issue_type"] == "MISSING_FILE"
    assert item["action_taken"] == "SKIPPED_UNTOUCHED"


def test_migration_reporter_writes_json_and_markdown(tmp_path: Path) -> None:
    """Verify that reports are written to disk with valid JSON and Markdown contents."""
    reporter = MigrationReporter(
        command_name="migrate_files_to_lfenc02",
        mode="dry_run",
    )

    reporter.record_target(
        target_name="document.Document (document_file)",
        total_count=10,
        migrated=8,
        skipped=1,
        quarantined=1,
    )
    reporter.record_quarantine(
        model="document.Document",
        pk="1111-2222",
        field="document_file",
        path="missing.txt",
        issue_type="MISSING_FILE",
        error="File not found",
    )

    json_path, md_path = reporter.write_reports(output_dir=tmp_path)

    assert json_path.exists()
    assert md_path.exists()

    # Verify JSON structure
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["command"] == "migrate_files_to_lfenc02"
    assert data["mode"] == "dry_run"
    assert data["summary"]["total_scanned"] == 10
    assert data["summary"]["total_migrated"] == 8
    assert len(data["quarantined_items"]) == 1

    # Verify Markdown contains table
    md_content = md_path.read_text(encoding="utf-8")
    assert "# Migration Report: `migrate_files_to_lfenc02`" in md_content
    assert "document.Document (document_file)" in md_content
    assert "MISSING_FILE" in md_content

    # Verify latest pointer exists
    latest_json = tmp_path / "migrate_files_to_lfenc02_latest.json"
    assert latest_json.exists()
