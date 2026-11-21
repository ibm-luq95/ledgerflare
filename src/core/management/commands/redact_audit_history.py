"""Command to redact sensitive plaintext in auditlog history."""

from __future__ import annotations

from typing import Any

from auditlog.models import LogEntry
from django.core.management.base import BaseCommand

from core.signals.auditlog import sanitize_log_entry


class Command(BaseCommand):
    """Redact historical plaintext values in auditlog changes."""

    help = "Redact plaintext values in auditlog for encrypted fields."

    def add_arguments(self, parser: Any) -> None:
        """Add CLI arguments for redact command."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Scan audit entries without modifying them.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Redact sensitive field values in audit history."""
        is_dry_run = options.get("dry_run", False)

        entries = LogEntry.objects.all()
        redacted_count = 0

        for entry in entries.iterator(chunk_size=500):
            modified = sanitize_log_entry(entry)
            if modified:
                redacted_count += 1
                if not is_dry_run:
                    entry.save(update_fields=["changes", "serialized_data"])

        if is_dry_run:
            self.stdout.write(
                f"AUDIT REDACTION DRY RUN COMPLETE: {redacted_count} "
                "entries identified for redaction."
            )
        else:
            self.stdout.write(
                f"AUDIT REDACTION COMPLETE: {redacted_count} entries redacted."
            )
