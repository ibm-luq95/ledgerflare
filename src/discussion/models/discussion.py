
from django.db import models
from django.utils.translation import gettext as _

from beach_wood_user.models import BWUser
from core.constants.file_types_validation import IMAGES_AND_DOCS_FT
from core.fields import EncryptedFileField, EncryptedTextField
from core.models.mixins import (
    BaseModelMixin,
    SanitizeHTMLFieldsMixin,
    StrModelMixin,
    TeamMembersMixin,
)
from core.utils import FileValidator
from discussion.models.manager import RepliesManager
from job.models import JobProxy
from special_assignment.models import SpecialAssignmentProxy


file_validator = FileValidator(
    max_size=100 * 1024 * 1024,
    content_types=IMAGES_AND_DOCS_FT,
    scan_malware=True,
)


class Discussion(BaseModelMixin, TeamMembersMixin, StrModelMixin, SanitizeHTMLFieldsMixin):
    SANITY_HTML_FIELDS = ("body",)
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
    body = EncryptedTextField(_("body"))
    replies = models.ForeignKey(
        to="self",
        on_delete=models.CASCADE,
        related_name="discussion_replies",
        null=True,
        blank=True,
        help_text=_("Optional, This will use when you want to reply on custom reply"),
    )
    attachment = EncryptedFileField(
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
        ordering = ["created_at"]

    def for_what(self) -> SpecialAssignmentProxy | JobProxy | None:
        if self.job:
            return self.job
        if self.special_assignment:
            return self.special_assignment
        return None

    def get_absolute_url(self) -> str:
        target = self.for_what()
        if target:
            return target.get_absolute_url()
        return "#"
