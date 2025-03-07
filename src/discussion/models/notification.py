from django.db import models
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from beach_wood_user.models import BWUser
from core.models.mixins import BaseModelMixin
from discussion.models import DiscussionProxy
from job.models import JobProxy
from special_assignment.models import SpecialAssignmentProxy


class DiscussionNotification(BaseModelMixin):
    discussion = models.ForeignKey(
        to=DiscussionProxy, related_name="notifications", on_delete=models.CASCADE
    )
    msg = models.CharField(
        _("message"),
        max_length=250,
        null=True,
        blank=True,
        default=_("You have notification"),
    )
    job = models.ForeignKey(
        to=JobProxy,
        related_name="notifications",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    special_assignment = models.ForeignKey(
        to=SpecialAssignmentProxy,
        related_name="notifications",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    is_read = models.BooleanField(_("is read"), default=False)
    recipient = models.ForeignKey(
        to=BWUser, related_name="notifications", on_delete=models.CASCADE
    )

    def get_url(self) -> str:
        if self.job:
            return reverse_lazy("dashboard:job:details", kwargs={"pk": self.job.pk})
        elif self.special_assignment:
            return reverse_lazy(
                "dashboard:special_assignment:details",
                kwargs={"pk": self.special_assignment.pk},
            )

    @property
    def notification_type(self) -> str:
        if self.job:
            return "job"
        elif self.special_assignment:
            return "special_assignment"
        else:
            return "discussion"

    @property
    def full_message(self) -> str:
        pass

    class Meta(BaseModelMixin.Meta):
        ordering = ["-created_at"]
        verbose_name = _("discussion notification")
        verbose_name_plural = _("discussion notifications")
        indexes = [
            models.Index(name="notification_is_read_idx", fields=["is_read"]),
            models.Index(name="job_notification_idx", fields=["job"]),
            models.Index(name="sa_notification_idx", fields=["special_assignment"]),
            models.Index(name="recipient_idx", fields=["recipient"]),
        ]
