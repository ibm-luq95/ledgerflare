# -*- coding: utf-8 -*-#
from __future__ import annotations

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core.admin import BWBaseAdminModelMixin
from lf_notifications.models import NotificationPreferenceProxy

@admin.register(NotificationPreferenceProxy)
class NotificationPreferenceAdmin(BWBaseAdminModelMixin):
    list_display = [
        "user",
        "notification_type",
        "channel",
        "enabled",
        "created_at",
    ]
    list_filter = ["channel", "enabled", "notification_type"] + BWBaseAdminModelMixin.list_filter
    search_fields = ["user__email", "user__first_name", "user__last_name", "notification_type"]
