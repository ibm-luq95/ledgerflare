"""Provide mixin for retrieving related notes and documents across models."""

from __future__ import annotations

from typing import Any

from django.db import DatabaseError
from django.db.models import Q

from core.utils.developments.debugging_print_object import DebuggingPrint


class BWGetRelatedNotesAndDocuments:
    """Provide helper methods for retrieving related notes and documents."""

    def related_for_job(self) -> dict[str, Any]:
        """Return an empty dictionary for job-related items."""
        return {}

    def related_for_clients(self) -> dict[str, Any]:
        """Retrieve related notes and documents for clients."""
        try:
            from document.models.document_proxy import DocumentProxy
            from note.models.note_proxy import NoteProxy

            notes = (
                NoteProxy.objects
                .all()
                .filter(
                    Q(client=self) | Q(job__client=self) | Q(task__job__client=self)
                )
                .distinct()
            )
            documents = (
                DocumentProxy.objects
                .all()
                .filter(
                    Q(client=self) | Q(job__client=self) | Q(task__job__client=self)
                )
                .distinct()
            )
        except DatabaseError, AttributeError, ValueError, TypeError:
            DebuggingPrint.print_exception()
            from document.models.document_proxy import DocumentProxy
            from note.models.note_proxy import NoteProxy

            return {
                "notes": NoteProxy.objects.none(),
                "documents": DocumentProxy.objects.none(),
            }
        else:
            return {
                "notes": notes,
                "documents": documents,
            }

    def get_all_related_notes_and_documents(self) -> dict[str, Any]:
        """Retrieve related notes and documents based on RELATED_ITEM_ID."""
        if hasattr(self, "_cached_related_notes_and_docs"):
            return self._cached_related_notes_and_docs

        if getattr(self, "RELATED_ITEM_ID", None) == "client":
            data = self.related_for_clients()
            self._cached_related_notes_and_docs = data
            return data

        return {}
