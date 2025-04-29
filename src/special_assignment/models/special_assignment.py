# -*- coding: utf-8 -*-#
from django.conf import settings
from django.db import models
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from client.models import ClientProxy
from core.choices.special_assignment import SpecialAssignmentStatusEnum
from core.constants.file_types_validation import IMAGES_AND_DOCS_FT
from core.models.mixins import (
    BaseModelMixin,
    StartAndDueDateMixin,
    TeamMembersMixin,
    StrModelMixin,
)
from core.models.mixins.cron_column_mixin import CronColumnMixin
from core.utils import FileValidator
from job.models import JobProxy
from special_assignment.models.manager import SpecialAssignmentsManager

file_validator = FileValidator(max_size=1024 * 1000, content_types=IMAGES_AND_DOCS_FT)


class SpecialAssignment(
    BaseModelMixin, StartAndDueDateMixin, TeamMembersMixin, CronColumnMixin, StrModelMixin
):
    """Represents a special assignment.

    This class defines a special assignment with attributes such as client, job, title, body, status, attachment, notes, is_seen, and assigned_by.

    Attributes:
        client (ForeignKey to ClientProxy): The client associated with the assignment.
        job (ForeignKey to JobProxy): The job associated with the assignment.
        title (CharField): The title of the assignment.
        body (TextField): The main content of the assignment.
        status (CharField): The status of the assignment.
        attachment (FileField): File attachment for the assignment.
        notes (TextField): Additional notes for the assignment.
        is_seen (BooleanField): Indicates if the assignment has been seen.
        assigned_by (ForeignKey to User): User who assigned the special assignment.

    Methods:
        get_absolute_url(self): Returns the absolute URL for the special assignment.
    """

    client = models.ForeignKey(
        to=ClientProxy,
        on_delete=models.PROTECT,
        related_name="special_assignments",
        null=True,
        blank=True,
        db_index=True,
    )
    job = models.ForeignKey(
        to=JobProxy,
        on_delete=models.PROTECT,
        related_name="special_assignments",
        null=True,
        blank=True,
        db_index=True,
    )
    title = models.CharField(_("title"), max_length=100, null=False, blank=False)
    body = models.TextField(_("body"))
    status = models.CharField(
        _("status"),
        max_length=15,
        choices=SpecialAssignmentStatusEnum.choices,
        default=SpecialAssignmentStatusEnum.NOT_STARTED,
        db_index=True,
    )
    attachment = models.FileField(
        _("attachment"),
        upload_to="special_assignment_attachments/",
        null=True,
        blank=True,
        validators=[file_validator],
    )
    notes = models.TextField(_("notes"), null=True, blank=True)
    is_seen = models.BooleanField(_("is seen"), default=False, db_index=True)
    assigned_by = models.ForeignKey(
        verbose_name=_("assigned by"),
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="requested_assignments",
        help_text=_("readonly, you cant modified it"),
        editable=False,
        null=True,
        blank=True,
        db_index=True,
    )
    assigned_to = models.ForeignKey(
        verbose_name=_("assigned to"),
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="assigned_assignments",
    )

    # objects = SpecialAssignmentsManager()

    class Meta(BaseModelMixin.Meta):
        ordering = ["title"]

    def get_absolute_url(self):
        reverse_lazy("dashboard:special_assignment:details", kwargs={"pk": self.pk})
