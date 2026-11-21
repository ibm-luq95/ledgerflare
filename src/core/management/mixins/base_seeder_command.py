"""Base mixin for data seeder management commands."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from django.core.management.base import BaseCommand, CommandParser
from django.utils.translation import gettext as _
from faker import Faker

from core.management.mixins.command_stdout import CommandStdOutputMixin
from core.management.mixins.production_guard import ProductionGuardCommandMixin


class BaseSeederCommandMixin(
    ProductionGuardCommandMixin, CommandStdOutputMixin, BaseCommand, ABC
):
    """Base mixin providing common flags and Faker instances for seeders."""

    FAKER_OBJ: ClassVar[Faker] = Faker(locale="en_US")

    def add_arguments(self, parser: CommandParser) -> None:
        """Add CLI arguments for number of records to seed."""
        super().add_arguments(parser)
        parser.add_argument(
            "--number", "-n", type=str, help=_("Number of records"), required=True
        )

    @abstractmethod
    def handle(self, *args: Any, **options: Any) -> Any:
        """Execute seeding logic."""

