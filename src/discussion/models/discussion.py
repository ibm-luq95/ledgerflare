# -*- coding: utf-8 -*-#

from django.db import models
from django.utils.translation import gettext as _

from beach_wood_user.models import BWUser
from core.constants.file_types_validation import IMAGES_AND_DOCS_FT
from core.models.mixins import BaseModelMixin, TeamMembersMixin, StrModelMixin
from core.utils import FileValidator
from discussion.models.manager import RepliesManager
from job.models import JobProxy
from special_assignment.models import SpecialAssignmentProxy

file_validator = FileValidator(max_size=1024 * 10000, content_types=IMAGES_AND_DOCS_FT)


class Discussion(BaseModelMixin, TeamMembersMixin, StrModelMixin):
    special_assignment = models.ForeignKey(
        to=SpecialAssignmentProxy,
        on_delete=models.CASCADE,
        related_name="discussions",
        null=True,
        blank=True,
    )
    job = models.ForeignKey(
        to=JobProxy,
        on_delete=models.CASCADE,
        related_name="discussions",
        null=True,
        blank=True,
    )
    body = models.TextField(_("body"))
    replies = models.ForeignKey(
        to="self",
        on_delete=models.CASCADE,
        related_name="discussion_replies",
        null=True,
        blank=True,
        help_text=_("Optional, This will use when you want to reply on custom reply"),
    )
    attachment = models.FileField(
        _("attachment"),
        upload_to="discussion_attachment/",
        null=True,
        blank=True,
        validators=[file_validator],
    )
    is_seen = models.BooleanField(_("is_seen"), default=False)
    sender = models.ForeignKey(
        to=BWUser,
        on_delete=models.CASCADE,
        related_name="submitted_discussions",
        null=True,
        blank=True,
    )

    objects = RepliesManager()

    class Meta(BaseModelMixin.Meta):
        ordering = ["-created_at"]
