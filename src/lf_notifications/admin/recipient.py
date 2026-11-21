# -*- coding: utf-8 -*-#
from __future__ import annotations

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core.admin import BWBaseAdminModelMixin
from lf_notifications.models import NotificationRecipientProxy

@admin.register(NotificationRecipientProxy)
class NotificationRecipientAdmin(BWBaseAdminModelMixin):
    list_display = [
        "recipient",
        "notification",
        "is_read",
        "is_seen",
        "read_at",
        "created_at",
    ]
    list_filter = ["is_read", "is_seen"] + BWBaseAdminModelMixin.list_filter
    search_fields = ["recipient__email", "recipient__first_name", "recipient__last_name", "notification__message_template"]
    readonly_fields = ["read_at", "seen_at"]
