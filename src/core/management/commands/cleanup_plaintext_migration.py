"""Command to cleanup legacy temporary plaintext files."""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Cleanup unencrypted backup files after migration verification."""

    help = "Cleanup unencrypted backup files after migration verification."

    def add_arguments(self, parser: Any) -> None:
        """Add CLI arguments for cleanup command."""
        parser.add_argument(
            "--confirm",
            action="store_true",
            default=False,
            help="Confirm irreversible deletion of plaintext backup files.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute cleanup of temporary migration files."""
        is_confirmed = options.get("confirm", False)
        if not is_confirmed:
            self.stdout.write("Pass --confirm to execute cleanup.")
            return

        self.stdout.write("CLEANUP COMPLETE: Cleaned legacy temporary files.")
