# -*- coding: utf-8 -*-#
from __future__ import annotations

from typing import ClassVar

from django.db import models

from core.utils.html_sanitizer import sanitize_html


class SanitizeHTMLFieldsMixin(models.Model):
    """
    Abstract model mixin that automatically cleans configured HTML fields
    using nh3 prior to saving to the database.
    """

    SANITY_HTML_FIELDS: ClassVar[tuple[str, ...]] = ()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs) -> None:
        """Sanitize configured HTML fields before calling super().save()."""
        for field_name in self.SANITY_HTML_FIELDS:
            raw_value = getattr(self, field_name, None)
            if raw_value and isinstance(raw_value, str):
                setattr(self, field_name, sanitize_html(raw_value))
        super().save(*args, **kwargs)
