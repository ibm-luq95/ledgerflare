from __future__ import annotations

from important_contact.models.important_contact import ImportantContact


class ImportantContactProxy(ImportantContact):
    """Proxy model for ImportantContact providing domain helpers and guardian permission target."""

    class Meta(ImportantContact.Meta):
        proxy = True
        indexes = []
