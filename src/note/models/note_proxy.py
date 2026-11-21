from __future__ import annotations

from note.models.note import Note


class NoteProxy(Note):
    """Proxy model for Note providing domain helpers and guardian permission target."""

    class Meta(Note.Meta):
        proxy = True
        indexes = []
