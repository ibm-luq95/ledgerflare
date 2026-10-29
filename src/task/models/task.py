# -*- coding: utf-8 -*-#

from django.db import models
from django.utils.translation import gettext as _

from core.choices import TaskStatusEnum
from core.choices import TaskTypeEnum
from core.fields.encrypted_fields import EncryptedTextField
from core.models.mixins import BaseModelMixin
from core.models.mixins import SanitizeHTMLFieldsMixin
from core.models.mixins import StrModelMixin
from core.models.mixins.access_proxy_models_mixin import AccessProxyModelMixin
from core.models.mixins.cron_column_mixin import CronColumnMixin
from core.models.mixins.encrypted_model import EncryptedModelMixin
from job.models.job_proxy import JobProxy
from task.models.manager.tasks_manager import TaskManager


# class Task(BaseModelMixin, StartAndDueDateMixin, StrModelMixin, CreatedByMixin):
class Task(
    BaseModelMixin,
    AccessProxyModelMixin,
    CronColumnMixin,
    StrModelMixin,
    SanitizeHTMLFieldsMixin,
    EncryptedModelMixin,
):
    SANITY_HTML_FIELDS = ("additional_notes",)
    """Tasks for every job.

    This class represents a task in the system. It extends the `BaseModelMixin`, `AccessProxyModelMixin`, `CronColumnMixin`, and `StrModelMixin` classes.

    Attributes:
        job (ForeignKey): A foreign key to the `JobProxy` model representing the job associated with the task.
        title (CharField): ACharField representing the title of the task.
        task_type (CharField): ACharField representing the type of the task.
        status (CharField): ACharField representing the status of the task.
        is_completed (BooleanField): ABooleanField indicating whether the task is completed or not.
        hints (CharField): ACharField representing hints for the task.
        additional_notes (TextField): ATextField representing additional notes for the task.
        objects (TaskManager): The manager for the `Task` model.
    """

    """Tasks for every job

    Args:
        BaseModelMixin (models.Model): The base django model mixin
    """

    # def __init__(self, *args, **kwargs):
    #     super(Task, self).__init__(*args, **kwargs)
    #     self.__original_model = self.model

    job = models.ForeignKey(
        to=JobProxy,
        on_delete=models.PROTECT,
        related_name="tasks",
        null=True,
        blank=True,
        db_index=True,
    )
    title = models.CharField(_("title"), max_length=80, null=True)
    task_type = models.CharField(
        _("task type"),
        max_length=15,
        null=True,
        blank=True,
        choices=TaskTypeEnum.choices,
        db_index=True,
    )
    status = models.CharField(
        _("status"),
        max_length=15,
        null=True,
        blank=True,
        choices=TaskStatusEnum.choices,
        default=TaskStatusEnum.NOT_STARTED,
        db_index=True,
        # db_column="status"
    )
    is_completed = models.BooleanField(
        _("is completed"), default=False, editable=False, db_index=True
    )
    hints = EncryptedTextField(
        _("hints"),
        null=True,
        blank=True,
        help_text=_("Hints help to this task"),
    )
    additional_notes = EncryptedTextField(
        _("additional notes"),
        null=True,
        blank=True,
        help_text=_("Additional note for the task"),
    )
    objects = TaskManager()

    # items = models.ManyToManyField(to=TaskItem, related_name="task", blank=True)

    class Meta(BaseModelMixin.Meta):
        ordering = ["title"]
