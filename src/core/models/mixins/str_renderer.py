"""Model mixin providing safe string representation for models."""

from __future__ import annotations

import textwrap

from django.db import models

from core.constants.general import DEFAULT_SHORT_TRUNCATED_STRING


class StrModelMixin(models.Model):
    """Mixin class providing a safe string representation for model instances."""

    class Meta:
        """Meta options for abstract mixin."""

        abstract = True

    def __str__(self) -> str:
        """Return a shortened string representation of title, body, or name."""
        for attr in ("title", "body", "name"):
            val = getattr(self, attr, None)
            if val is not None and str(val).strip():
                return textwrap.shorten(
                    str(val),
                    width=DEFAULT_SHORT_TRUNCATED_STRING,
                    placeholder="...",
                )
        return ""
