"""
Module for managing model signals in enterprise-grade Django applications.
"""

from __future__ import annotations

import logging
from typing import Type, List, Dict, Any
from contextlib import AbstractContextManager
from django.db.models import Model
from django.db.models.signals import (
    pre_save,
    post_save,
    pre_delete,
    post_delete,
    m2m_changed,
)
from django.dispatch import Signal

# Configure structured logger
logger = logging.getLogger(__name__)

SUPPORTED_SIGNALS = [
    pre_save,
    post_save,
    pre_delete,
    post_delete,
    m2m_changed,
]


class ScopedSignalDisabler(AbstractContextManager):
    """
    Context manager to disable all major signals for a specific model.

    Ensures original signal handlers are restored after use.

    Parameters
    ----------
    model_class : Type[Model]
        The Django model whose signals will be disabled during fixture loading.
    signal_types : List[Signal], optional
        A list of signal types to disable. Defaults to all major signals.
    """

    def __init__(self, model_class: Type[Model], signal_types: List[Signal] | None = None):
        self.model_class: Type[Model] = model_class
        self.signal_types: List[Signal] = signal_types or SUPPORTED_SIGNALS
        self.saved_receivers: Dict[Signal, List[Any]] = {}

    def __enter__(self) -> ScopedSignalDisabler:
        logger.info(
            "ScopedSignalDisabler: Disabling signals for model '%s'.",
            self.model_class.__name__,
        )
        for signal in self.signal_types:
            self.saved_receivers[signal] = signal.receivers[:]
            signal.receivers = [
                r for r in signal.receivers if not self._is_receiver_for_model(r)
            ]
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        for signal in self.signal_types:
            signal.receivers = self.saved_receivers.get(signal, [])
        logger.info(
            "ScopedSignalDisabler: Signals for model '%s' have been restored.",
            self.model_class.__name__,
        )

    def _is_receiver_for_model(self, receiver: Any) -> bool:
        try:
            _, _, func = receiver  # Unpack weak reference tuple
            sender = getattr(func, "sender", None)
            return sender is not None and issubclass(sender, self.model_class)
        except Exception as e:
            logger.warning("Unable to inspect receiver: %s", str(e))
            return False
