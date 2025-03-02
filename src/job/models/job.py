# -*- coding: utf-8 -*-#

from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext as _

from client.models import ClientProxy
from core.choices import JobStateEnum
from core.choices import JobStatusEnum
from core.choices import JobTypeEnum
from core.choices.fiscal_year import FiscalYearEnum
from core.choices.months import MonthChoices
from core.models.mixins import BaseModelMixin
from core.models.mixins import StartAndDueDateMixin
from core.models.mixins import StrModelMixin
from core.models.mixins.access_proxy_models_mixin import AccessProxyModelMixin
from core.models.mixins.cron_column_mixin import CronColumnMixin
from core.models.mixins.validate_due_date import ValidateDueDateMixin
from job_category.models import JobCategory

# from task.models import Task
from .help_messages import JOB_HELP_MESSAGES
from .manager.job_manager import JobManager


class Job(
    ValidateDueDateMixin,
    BaseModelMixin,
    StartAndDueDateMixin,
    AccessProxyModelMixin,
    CronColumnMixin,
    StrModelMixin,
):
    """This is the job for every bookkeeper and assistant.

    Attributes:
        client (ClientProxy): The client associated with the job.
        managed_by (User): The user who manages the job.
        title (str): The title of the job.
        slug (str): The slug of the job.
        period_year (str): The fiscal year of the job.
        period_month (str): The fiscal month of the job.
        description (str): The description of the job.
        job_type (JobTypeEnum): The type of the job.
        status (JobStatusEnum): The status of the job.
        state (JobStateEnum): The state of the job.
        categories (JobCategory): The categories associated with the job.
        note (str): The note for the job.
        is_created_from_template (bool): Indicates if the job is created from a template.

    Methods:
        get_all_not_completed_tasks(): Returns all the tasks that are not completed.
        is_job_pass_due(): Checks if the job has passed its due date.
        get_absolute_url(): Returns the absolute URL of the job.
    """

    """This is the job for every bookkeeper and assistant

    Args:
        BaseModelMixin (models.Model): Django model base mixin
    """

    client = models.ForeignKey(
        to=ClientProxy,
        on_delete=models.PROTECT,  # TODO: check if this should be null not protected
        null=True,
        blank=True,
        related_name="jobs",
        help_text=JOB_HELP_MESSAGES.get("client"),
    )
    managed_by = models.ForeignKey(
        to=get_user_model(),
        on_delete=models.CASCADE,
        related_name="jobs",
        null=True,
        blank=True,
        help_text=JOB_HELP_MESSAGES.get("managed_by"),
    )
    title = models.CharField(
        _("title"), max_length=100, null=False, help_text=JOB_HELP_MESSAGES.get("title")
    )
    slug = models.SlugField(
        _("slug"), max_length=250, null=True, blank=True, editable=False
    )
    period_year = models.CharField(
        _("period year"),
        max_length=4,
        null=True,
        blank=True,
        db_index=True,
        choices=FiscalYearEnum.choices,
        help_text=JOB_HELP_MESSAGES.get("period_year"),
    )
    period_month = models.CharField(
        _("period month"),
        max_length=2,
        null=True,
        blank=True,
        db_index=True,
        choices=MonthChoices.choices,
        help_text=JOB_HELP_MESSAGES.get("period_month"),
    )
    description = models.TextField(
        _("description"),
        null=True,
        blank=True,
        help_text=JOB_HELP_MESSAGES.get("description"),
    )
    job_type = models.CharField(
        _("job type"),
        choices=JobTypeEnum.choices,
        # default=JobTypeEnum.NO_TYPE,
        max_length=20,
        help_text=JOB_HELP_MESSAGES.get("job_type"),
        db_index=True,
    )
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=JobStatusEnum.choices,
        # default=JobStatusEnum.NOT_STARTED,
        help_text=JOB_HELP_MESSAGES.get("status"),
        db_index=True,
    )
    state = models.CharField(
        _("state"),
        max_length=20,
        choices=JobStateEnum.choices,
        default=JobStateEnum.ONGOING,
        help_text=JOB_HELP_MESSAGES.get("state"),
        null=True,
        blank=True,
        db_index=True,
    )
    categories = models.ManyToManyField(
        to=JobCategory,
        related_name="jobs",
        blank=True,
        help_text=JOB_HELP_MESSAGES.get("categories"),
        db_index=True,
    )
    is_scheduled = models.BooleanField(
        _("scheduled"),
        null=True,
        # blank=True,
        help_text=JOB_HELP_MESSAGES.get("is_scheduled"),
    )
    scheduled_date = models.DateField(
        _("Scheduled date"),
        null=True,
        blank=True,
        help_text=JOB_HELP_MESSAGES.get("scheduled_date"),
    )

    # tasks = models.ManyToManyField(to=Task, help_text=JOB_HELP_MESSAGES.get("tasks"))
    note = models.TextField(
        _("note"), null=True, help_text=JOB_HELP_MESSAGES.get("note"), blank=True
    )
    is_created_from_template = models.BooleanField(
        _("is_created_from_template"), default=False, editable=False
    )
    objects = JobManager()
    all_objects = models.Manager()

    # objects = Manager()

    # not_filtered_objects = JobManager()
    # objects = JobManager()

    class Meta(BaseModelMixin.Meta):
        ordering = ["title"]

        permissions = BaseModelMixin.Meta.permissions + [
            ("list_abstract_job_template", "List abstract job template")
        ]
        indexes = [
            models.Index(name="jobs_is_scheduled_idx", fields=["is_scheduled"]),
            models.Index(name="scheduled_date_idx", fields=["scheduled_date"]),
        ]

    # def get_absolute_url(self):
    #     return reverse("manager:jobs:details", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Job, self).save(*args, **kwargs)

    def get_all_not_completed_tasks(self):
        filtered = filter(lambda task: task.is_completed is False, self.tasks.all())
        return tuple(filtered)

    def is_job_pass_due(self) -> bool:
        now = timezone.now().date()
        if self.due_date > now:
            return True
        else:
            return False

    def get_absolute_url(self):
        reverse_lazy("dashboard:job:details", kwargs={"pk": self.pk})

    # def get_all_assigned_users(self) -> list:
    #     all_users = []
    #     if self.bookkeeper.all():
    #         for bookkeeper in self.bookkeeper.all():
    #             all_users.append(bookkeeper)
    #
    #     if self.assistants.all():
    #         for assistant in self.assistants.all():
    #             all_users.append(assistant)
    #     return all_users
