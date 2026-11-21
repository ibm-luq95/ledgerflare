from __future__ import annotations

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models.mixins import BaseModelMixin

class NotificationRecipient(BaseModelMixin):
    notification = models.ForeignKey(
        to="lf_notifications.NotificationProxy",
        on_delete=models.CASCADE,
        related_name="recipients",
    )
    recipient = models.ForeignKey(
        to="beach_wood_user.BWUser",
        on_delete=models.CASCADE,
        related_name="received_notifications",
    )
    is_read = models.BooleanField(
        _("is read"),
        default=False,
    )
    read_at = models.DateTimeField(
        _("read at"),
        null=True,
        blank=True,
        default=None,
    )
    is_seen = models.BooleanField(
        _("is seen"),
        default=False,
    )
    seen_at = models.DateTimeField(
        _("seen at"),
        null=True,
        blank=True,
        default=None,
    )

    class Meta(BaseModelMixin.Meta):
        ordering = ["-created_at"]
        verbose_name = _("notification recipient")
        verbose_name_plural = _("notification recipients")
        db_table = "lf_notifications_recipient"
        constraints = [
            models.UniqueConstraint(
                fields=["notification", "recipient"],
                name="unique_notification_recipient",
            )
        ]
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"], name="lf_notif_rec_unread_idx"),
            models.Index(fields=["recipient", "is_seen"], name="lf_notif_rec_seen_idx"),
        ]

    def mark_as_read(self) -> None:
        self.is_read = True
        self.read_at = timezone.now()
        self.save()

    def mark_as_seen(self) -> None:
        self.is_seen = True
        self.seen_at = timezone.now()
        self.save()

    def __str__(self) -> str:
        return f"{self.recipient} - Read: {self.is_read}"

class NotificationRecipientProxy(NotificationRecipient):
    class Meta(NotificationRecipient.Meta):
        proxy = True
        indexes = []
