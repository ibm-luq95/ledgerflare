"""Proxy model for Document."""

from __future__ import annotations

from typing import Any, ClassVar

from django.urls import reverse_lazy

from document.models.document import Document


class DocumentProxy(Document):
    """Proxy model for Document to enforce guardian object permissions."""

    class Meta(Document.Meta):
        """Meta options for DocumentProxy."""

        proxy = True

    def get_absolute_url(self) -> str:
        """Return the absolute URL for the document viewer."""
        return str(
            reverse_lazy("dashboard:document:view", kwargs={"pk": self.pk})
        )
