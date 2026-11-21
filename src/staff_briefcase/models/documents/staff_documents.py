import secrets

from django.contrib import admin
from django.db import models
from django.utils.translation import gettext as _

from core.fields import EncryptedFileField
from core.models.mixins import BaseModelMixin


def saved_document_file_path(instance, filename):
    file_suffix = secrets.token_urlsafe(7)
    return f"staff_documents/{file_suffix}_{filename}"


class StaffDocuments(BaseModelMixin):
    """Represents a staff document.

    This class defines a staff document with attributes such as title and document file.

    Attributes:
        title (CharField): The title of the document.
        document_file (EncryptedFileField): The encrypted file associated with the document.

    Methods:
        get_briefcase(self): Retrieves the associated briefcase for the staff document.
    """

    title = models.CharField(_("title"), max_length=250, null=True, blank=True)
    document_file = EncryptedFileField(
        _("document file"), upload_to=saved_document_file_path
    )

    @admin.display(description=_("briefcase"))
    def get_briefcase(self):
        if hasattr(self, "briefcase"):
            return self.briefcase.get()
        return None

    class Meta:
        ordering = ["title"]
        verbose_name = _("Staff Document")
        verbose_name_plural = _("Staff Documents")
