import textwrap

from django.contrib import admin
from django.db import models
from django.utils.translation import gettext as _

from core.fields import EncryptedTextField
from core.models.mixins import BaseModelMixin, StrModelMixin


class StaffNotes(BaseModelMixin, StrModelMixin):
    """Represents a staff note.

    This class defines a staff note with attributes such as title and note content.

    Attributes:
        title (CharField): The title of the note.
        note (EncryptedTextField): The encrypted main content of the note.

    Methods:
        note_body(self): Displays a shortened version of the note content.
        get_briefcase(self): Retrieves the associated briefcase for the staff note.
    """

    title = models.CharField(_("title"), max_length=250, null=True, blank=True)
    note = EncryptedTextField(_("Note"))

    @admin.display(description=_("Note body"))
    def note_body(self):
        return textwrap.shorten(self.note, width=20, placeholder="...")

    @admin.display(description=_("briefcase"))
    def get_briefcase(self):
        if hasattr(self, "briefcase"):
            return self.briefcase.get()
        return None

    class Meta:
        verbose_name = _("Staff Note")
        verbose_name_plural = _("Staff Notes")
        ordering = ["title"]
