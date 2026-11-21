from __future__ import annotations

from typing import Any
from itertools import chain

from django.db.models import QuerySet, Model

from beach_wood_user.models import BWUser
from core.utils.developments.debugging_print_object import DebuggingPrint
from lf_notifications.models import NotificationRecipientProxy


class LedgerFlareUserUtils:
    def __init__(self, user: BWUser):
        self.user: BWUser = user

    def get_all_not_read_notifications(self) -> QuerySet[NotificationRecipientProxy]:
        return NotificationRecipientProxy.objects.filter(
            recipient=self.user, is_read=False
        ).select_related("notification", "notification__actor")

    def get_all_notifications(self) -> QuerySet[NotificationRecipientProxy]:
        return NotificationRecipientProxy.objects.filter(
            recipient=self.user
        ).select_related("notification", "notification__actor")

    @property
    def get_all_total_not_read_notifications(self) -> int:
        return NotificationRecipientProxy.objects.filter(
            recipient=self.user, is_read=False
        ).count()
