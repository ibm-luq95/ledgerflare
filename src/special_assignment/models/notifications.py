from django.urls import reverse_lazy

from beach_wood_user.models import BWUser
from core.models.mixins import BaseModelMixin
from django.utils.translation import gettext as _
from django.db import models

from special_assignment.models import SpecialAssignmentProxy


class SpecialAssignmentNotification(BaseModelMixin):
    special_assignment = models.ForeignKey(
        SpecialAssignmentProxy,
        on_delete=models.CASCADE,
        related_name="special_assignment_notifications",
    )
    msg = models.CharField(
        _("message"),
        max_length=250,
        null=True,
        blank=True,
        default=_("You assigned a new special assignment"),
    )
    recipient = models.ForeignKey(
        to=BWUser,
        related_name="assigned_notifications",
        on_delete=models.CASCADE,
    )
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return (
            _("Special Assignment Notification for: ")
            + f"{self.recipient} - {self.special_assignment}"
        )

    class Meta(BaseModelMixin.Meta):
        ordering = ["-created_at"]
        verbose_name = _("special assignment notification")
        verbose_name_plural = _("special assignment notifications")
        indexes = [
            models.Index(name="sp_notification_is_read_idx", fields=["is_read"]),
            models.Index(name="special_assignment_idx", fields=["special_assignment"]),
            models.Index(name="sp_recipient_idx", fields=["recipient"]),
        ]

    def get_absolute_url(self):
        return reverse_lazy(
            "dashboard:special_assignment:details",
            kwargs={"pk": self.special_assignment.pk},
        )
