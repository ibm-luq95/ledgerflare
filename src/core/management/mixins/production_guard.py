"""Mixin to prevent destructive command execution in production."""
from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.management.base import CommandError, CommandParser


class ProductionGuardCommandMixin:
    """Safety guardrail for destructive or heavy management commands."""

    def add_arguments(self, parser: CommandParser) -> None:
        """Add --confirm-production argument."""
        super().add_arguments(parser)  # type: ignore[misc]
        parser.add_argument(
            "--confirm-production",
            action="store_true",
            default=False,
            help="Confirmation required for destructive commands in production.",
        )

    def execute(self, *args: Any, **options: Any) -> Any:
        """Verify safety guard before command execution."""
        env = getattr(settings, "ENVIRONMENT", "").lower()
        is_production = env == "production" or not getattr(settings, "DEBUG", True)
        if is_production and not options.get("confirm_production"):
            msg = "Destructive command requires '--confirm-production' in production."
            raise CommandError(msg)
        return super().execute(*args, **options)  # type: ignore[misc]
