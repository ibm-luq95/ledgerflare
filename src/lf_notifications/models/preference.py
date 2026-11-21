from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.mixins import BaseModelMixin

class NotificationChannelChoices(models.TextChoices):
    IN_APP = "in_app", _("In-App")
    EMAIL = "email", _("Email")
    SMS = "sms", _("SMS")
    PUSH = "push", _("Push Notification")

class NotificationPreference(BaseModelMixin):
    user = models.ForeignKey(
        to="beach_wood_user.BWUser",
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    notification_type = models.CharField(
        _("notification type"),
        max_length=50,
    )
    channel = models.CharField(
        _("channel"),
        max_length=20,
        choices=NotificationChannelChoices.choices,
        default=NotificationChannelChoices.IN_APP,
    )
    enabled = models.BooleanField(
        _("enabled"),
        default=True,
    )

    class Meta(BaseModelMixin.Meta):
        verbose_name = _("notification preference")
        verbose_name_plural = _("notification preferences")
        db_table = "lf_notifications_preference"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "notification_type", "channel"],
                name="unique_user_type_channel_pref",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user} - {self.notification_type} - {self.channel}: {self.enabled}"

class NotificationPreferenceProxy(NotificationPreference):
    class Meta(NotificationPreference.Meta):
        proxy = True
        indexes = []
