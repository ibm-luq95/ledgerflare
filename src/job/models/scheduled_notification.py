from beach_wood_user.models import BWUser
from core.models.mixins import BaseModelMixin
from django.db import models
from django.utils.translation import gettext as _

from job.models import JobProxy


class ScheduledNotification(BaseModelMixin):
    job = models.ForeignKey(
        to=JobProxy, on_delete=models.CASCADE, related_name="scheduled_notifications"
    )
    user = models.ForeignKey(
        to=BWUser, on_delete=models.CASCADE, related_name="scheduled_notifications"
    )
    is_seen = models.BooleanField(_("seen"), default=False)

    class Meta(BaseModelMixin.Meta):
        indexes = [
            models.Index(name="job_scheduled_is_seen_idx", fields=["is_seen"]),
        ]
