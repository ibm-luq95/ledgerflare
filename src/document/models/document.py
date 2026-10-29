import secrets

from django.db import models
from django.utils.translation import gettext as _

from client.models import ClientProxy
from core.choices import DocumentSectionEnum
from core.fields import EncryptedFileField
from core.models.mixins import (
    BaseModelMixin,
    GeneralStatusFieldMixin,
    GetObjectSectionMixin,
    StrModelMixin,
)
from job.models import JobProxy
from task.models import TaskProxy


def saved_document_file_path(instance, filename):
    file_suffix = secrets.token_urlsafe(7)
    return f"documents/{file_suffix}_{filename}"


class Document(
    BaseModelMixin, GetObjectSectionMixin, GeneralStatusFieldMixin, StrModelMixin
):
    title = models.CharField(
        _("title"), max_length=70, null=False, blank=False, db_index=True
    )
    document_section = models.CharField(
        _("document section"),
        max_length=15,
        null=True,
        blank=True,
        choices=DocumentSectionEnum.choices,
        db_index=True,
        editable=False,
    )
    document_file = EncryptedFileField(
        _("document file"),
        upload_to=saved_document_file_path,
    )

    client = models.ForeignKey(
        to=ClientProxy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )
    job = models.ForeignKey(
        to=JobProxy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )
    task = models.ForeignKey(
        to=TaskProxy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )

    class Meta(BaseModelMixin.Meta):
        ordering = ["title"]

    def save(self, *args, **kwargs):
        if self.job:
            self.document_section = DocumentSectionEnum.JOB
        elif self.task:
            self.document_section = DocumentSectionEnum.TASK
        elif self.client:
            self.document_section = DocumentSectionEnum.CLIENT
        super().save(*args, **kwargs)

    # def delete(self, *args, **kwargs):
    #     self.document_file.storage.delete(self.document_file.name)
    #     super(Documents, self).delete(*args, **kwargs)
