"""
Module containing reusable context managers with enhanced logging.
"""

from __future__ import annotations

import logging
from contextlib import ExitStack
from typing import List, Type, Any
from django.db.models import Model

from core.utils.signal_handlers import ScopedSignalDisabler

logger = logging.getLogger(__name__)


class ExitStackWithLogging(ExitStack):
    """
    An ExitStack subclass that logs when entering and exiting the stack.

    This is useful for tracking execution flow in enterprise applications.

    Parameters
    ----------
    models : List[Type[Model]]
        A list of models for which to disable signals inside the stack.
    """

    def __init__(self, models: List[Type[Model]]):
        super().__init__()
        self.models = models

    def __enter__(self) -> ExitStackWithLogging:
        """
        Enters the context and registers ScopedSignalDisabler for each model.

        Returns
        -------
        ExitStackWithLogging
            Returns self for chaining.
        """
        logger.info("Entering context to disable signals for %d models.", len(self.models))
        for model in self.models:
            logger.debug("Registering signal disabler for model: %s", model.__name__)
            self.enter_context(ScopedSignalDisabler(model))
        return super().__enter__()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """
        Exits the context and restores original signal handlers.

        Returns
        -------
        bool
            Result of base class exit handling.
        """
        logger.info("Exiting context; signals have been restored.")
        return super().__exit__(exc_type, exc_val, exc_tb)
