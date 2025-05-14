"""
Custom management command to load fixtures while selectively disabling model signals.

Supports:
- --fixture: one or more fixture files to load.
- --disable-signals: models whose signals should be disabled during load.
- --exclude: models or entire apps to exclude from being loaded.

This version follows enterprise Python development standards, including type hints,
structured logging, NumPy docstrings, and clean separation of concerns.
"""

from __future__ import annotations

import importlib
import logging
from typing import Any, List, Type, Optional

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandParser
from django.db.models import Model

from rich.console import Console
from rich.prompt import Confirm

from core.utils.context import ExitStackWithLogging
from core.utils.developments.debugging_print_object import DebuggingPrint

logger = logging.getLogger(__name__)
console = Console()


class Command(BaseCommand):
    """
    Management command to load fixtures with selective signal disabling and optional model/app exclusion.

    Attributes
    ----------
    help : str
        Description of the command shown in help text.
    """

    help = (
        "Load data from fixtures without triggering signals on specified models. "
        "Optionally exclude certain models or entire apps from being loaded."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Add command-line arguments.

        Parameters
        ----------
        parser : CommandParser
            The argument parser used to extract command-line inputs.
        """
        parser.add_argument(
            "--fixture",
            nargs="+",
            type=str,
            required=True,
            help="Fixture(s) to load.",
        )
        parser.add_argument(
            "--disable-signals",
            dest="disable_signals",
            nargs="*",
            type=str,
            default=None,  # Changed to None for required-like behavior
            help=(
                "List of fully qualified model names (e.g., app_label.ModelName)"
                " whose signals will be disabled during fixture loading. "
                "If not provided, you'll be prompted before proceeding."
            ),
        )
        parser.add_argument(
            "--exclude",
            dest="exclude",
            nargs="*",
            type=str,
            default=[],
            help=(
                "Exclude specific models or entire apps from being loaded. "
                "Format: 'app_label.ModelName' (e.g., 'auth.Permission') or just 'app_label' to exclude all models in the app."
            ),
        )

    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        """
        Execute the command logic.

        Prompts the user if `--disable-signals` is not provided.

        Parameters
        ----------
        args : Any
            Positional arguments passed via the command line.
        options : Any
            Keyword arguments parsed by the argument parser.

        Returns
        -------
        Optional[str]
            A message indicating the result of the operation.
        """
        fixtures: List[str] = options["fixture"]
        model_names: List[str] = options.get("disable_signals")
        exclude_labels: List[str] = options["exclude"]

        logger.info(
            "Starting fixture load with selective signal disabling and optional model/app exclusion."
        )

        try:
            # Check for --disable-signals flag
            if model_names is None:
                console.warning(
                    "[bold yellow]Warning:[/bold yellow] You did not specify any models to disable signals for."
                )
                confirmed = Confirm.ask(
                    "Are you sure you want to proceed with loading the fixture?",
                    default=False,
                    console=console,
                )
                if not confirmed:
                    self.stdout.write(self.style.WARNING("Operation cancelled by user."))
                    return "User cancelled fixture load."

            # Import and validate models for signal disabling
            disable_model_classes: List[Type[Model]] = []
            if model_names:
                for label in model_names:
                    try:
                        model_class = self._get_model_from_label(label)
                        disable_model_classes.append(model_class)
                    except Exception as e:
                        logger.error("Failed to resolve model '%s': %s", label, str(e))
                        self.stderr.write(
                            f"Error: Failed to resolve model '{label}': {str(e)}"
                        )
                        return f"Error processing model '{label}'"

            # Parse --exclude into strings like 'app_label' or 'app_label.ModelName'
            exclude_models: List[str] = []
            for label in exclude_labels:
                parts = label.split(".")
                if len(parts) == 1:
                    exclude_models.append(parts[0])
                elif len(parts) == 2:
                    exclude_models.append(f"{parts[0]}.{parts[1]}")
                else:
                    raise ValueError(
                        f"Invalid format for --exclude: '{label}'. "
                        "Expected 'app_label' or 'app_label.ModelName'."
                    )

            # Run fixture load within scoped signal disabling context
            with ExitStackWithLogging(disable_model_classes):
                call_command(
                    "loaddata",
                    *fixtures,
                    exclude=exclude_models,
                    verbosity=options.get("verbosity", 2),
                    traceback=options.get("traceback", True),
                    force_color=options.get("force_color", True),
                )

            self.stdout.write(self.style.SUCCESS("Fixture loaded successfully."))
            return "Fixture loaded successfully with signals selectively disabled."

        except Exception as e:
            logger.exception("Error occurred during fixture loading: %s", str(e))
            self.stderr.write(f"Error: {str(e)}")
            return f"Error: {str(e)}"

    def _get_model_from_label(self, label: str) -> Type[Model]:
        """
        Convert a string label into a Django model class.

        Parameters
        ----------
        label : str
            A string representing a model in the format 'app_label.ModelName'.

        Returns
        -------
        Type[Model]
            The resolved Django model class.

        Raises
        ------
        ImportError
            If the module cannot be imported.
        AttributeError
            If the model does not exist in the module.
        ValueError
            If the format is invalid or model is not a Django Model subclass.
        """
        try:
            app_label, model_name = label.split(".")
            module_path = f"{app_label}.models"
            module = importlib.import_module(module_path)
            model_class: Type[Model] = getattr(module, model_name)
            if not issubclass(model_class, Model):
                raise TypeError(f"'{label}' is not a valid Django model.")
            return model_class
        except ValueError as ve:
            raise ValueError(
                f"Invalid model label '{label}'. Expected format: 'app_label.ModelName'."
            ) from ve
        except Exception as ex:
            DebuggingPrint.print_exception()
