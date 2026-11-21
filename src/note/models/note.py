from django.db import models
from django.utils.translation import gettext as _

from client.models import ClientProxy
from core.choices import NoteSectionEnum
from core.constants.general import CON_JOB
from core.fields.encrypted_fields import EncryptedTextField
from core.models.mixins import (
    BaseModelMixin,
    GeneralStatusFieldMixin,
    GetObjectSectionMixin,
    SanitizeHTMLFieldsMixin,
    StrModelMixin,
)
from core.models.mixins.encrypted_model import EncryptedModelMixin
from job.models import JobProxy
from task.models import TaskProxy


class Note(
    BaseModelMixin,
    GetObjectSectionMixin,
    GeneralStatusFieldMixin,
    StrModelMixin,
    SanitizeHTMLFieldsMixin,
    EncryptedModelMixin,
):
    SANITY_HTML_FIELDS = ("body",)
    """Notes model for bookkeeper, assistant, and manager.

    This class represents a Note in the system with attributes such as title, body, client, job, task, and note_section.

    Attributes:
        title (CharField): The title of the note.
        body (TextField): The main body content of the note.
        client (ForeignKey): A foreign key to the ClientProxy model representing the client associated with the note.
        job (ForeignKey): A foreign key to the JobProxy model representing the job associated with the note.
        task (ForeignKey): A foreign key to the TaskProxy model representing the task associated with the note.
        note_section (CharField): Indicates the section of the note (choices: JOB, TASK, CLIENT).

    Methods:
        save(self, *args, **kwargs): Overrides the save method to set the note_section based on related objects.
    """

    """Notes model for bookkeeper, assistant, and manager

    Args:
        BaseModelMixin (models.Model): Django base model mixin
    """

    title = models.CharField(_("title"), max_length=60, null=False)
    body = EncryptedTextField(_("body"), null=False)
    client = models.ForeignKey(
        to=ClientProxy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notes",
    )
    job = models.ForeignKey(
        to=JobProxy, on_delete=models.SET_NULL, null=True, blank=True, related_name="notes"
    )
    task = models.ForeignKey(
        to=TaskProxy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notes",
    )
    note_section = models.CharField(
        _("note section"),
        max_length=15,
        null=True,
        blank=True,
        choices=NoteSectionEnum.choices,
        editable=False,
        db_index=True,
    )

    class Meta(BaseModelMixin.Meta):
        ordering = ["title"]
        verbose_name_plural = "notes"

    def save(self, *args, **kwargs):
        if self.job:
            self.note_section = NoteSectionEnum.JOB
        elif self.task:
            self.note_section = NoteSectionEnum.TASK
        elif self.client:
            self.note_section = NoteSectionEnum.CLIENT
        super().save(*args, **kwargs)
